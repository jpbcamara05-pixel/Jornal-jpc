"""Valor Econômico (fonte prioritária).

1. Feeds RSS por editoria (config/sources.yaml → valor.feeds) → lista do dia; a <description>
   já traz o texto integral dos artigos abertos (~50%).
2. Manifesto público da edição impressa (https://valor.globo.com/impresso/AAAAMMDD/, ~70 matérias)
   → prominence 0.85 (1.0 para itens de capa) e inclusão de matérias que não vieram no RSS.
3. Texto integral dos exclusivos para assinante via LoggedBrowser (cookie GLBID da Conta Globo).
   Sem anti-bot no globo.com; ritmo humano mesmo assim.
"""

from __future__ import annotations

import logging
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from ..models import Market, Source
from .base import Collector
from .rss import read_feed

log = logging.getLogger(__name__)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
# cabeçalhos (h2) do manifesto /impresso/ → editoria usada no feed
IMPRESSO_SECTIONS = {
    "primeira página": "capa", "brasil": "brasil", "política": "politica", "internacional": "mundo",
    "opinião": "opiniao", "empresas": "empresas", "agronegócios": "agronegocios", "finanças": "financas",
    "legislação & tributos": "legislacao", "especial": "especial", "eu &": "eu", "carreira": "carreira",
}


# blogs "ao vivo" (URL antiga reciclada), conteúdo patrocinado e seções fixas sem notícia
_SKIP_URL = ("/ao-vivo/", "/patrocinado/", "/conteudo-de-marca/")
_SKIP_TITLE = {"cartas de leitores", "correção", "frase do dia", "mais lidas"}


def _skip(url: str, title: str) -> bool:
    return any(x in url for x in _SKIP_URL) or title.strip().lower() in _SKIP_TITLE


class ValorCollector(Collector):
    name = "valor"
    source = Source.VALOR
    market = Market.LOCAL

    def collect(self, settings: dict, day: date) -> list:
        from .. import config
        cfg = config.load_yaml("sources.yaml")["valor"]
        weights = cfg.get("section_weights", {})
        by_url: dict[str, object] = {}
        for section, url in cfg["feeds"].items():
            for it in read_feed(url, settings["lookback_hours"]):
                if not it["url"] or it["url"] in by_url or _skip(it["url"], it["title"]):
                    continue
                a = self.make(it["url"], it["title"], summary=it["summary"], section=section,
                              published_at=it["published_at"], authors=it["authors"],
                              prominence=weights.get(section, 0.3), is_opinion=(section == "opiniao"))
                # description longa = artigo aberto com texto integral já no feed
                if it["summary"] and len(it["summary"]) > 1500:
                    a.body, a.word_count = it["summary"], len(it["summary"].split())
                by_url[it["url"]] = a

        self._apply_impresso(by_url, cfg, day)
        articles = list(by_url.values())
        return self._fetch_bodies(articles, cfg.get("max_full_text", 60))

    # ------------------------------------------------------------------ impresso
    def _apply_impresso(self, by_url: dict, cfg: dict, day: date) -> None:
        """Lê o manifesto da edição impressa e marca proeminência; adiciona matérias ausentes do RSS."""
        url = cfg["impresso_url"].format(yyyymmdd=day.strftime("%Y%m%d"))
        try:
            html = requests.get(url, headers=UA, timeout=30).text
        except Exception:
            log.warning("edição impressa indisponível: %s", url)
            return
        soup = BeautifulSoup(html, "html.parser")
        n_hit = n_new = 0
        heading = None  # o manifesto agrupa as matérias por caderno: h2 "Brasil", "Empresas", "Finanças"…
        for el in soup.find_all(["h2", "h3", "a"]):
            if el.name != "a":
                heading = IMPRESSO_SECTIONS.get(el.get_text(" ", strip=True).lower(), heading)
                continue
            href = el.get("href", "")
            if not re.search(r"valor\.globo\.com/.+\.ghtml$", href) or _skip(href, el.get_text(" ", strip=True)):
                continue
            front = "/impresso/noticia/" in href
            weight = cfg["impresso_front_weight"] if front else cfg["impresso_weight"]
            if href in by_url:
                by_url[href].prominence = max(by_url[href].prominence, weight)
                if by_url[href].section in ("capa", "impresso") and heading and heading != "capa":
                    by_url[href].section = heading
                n_hit += 1
            else:
                title = el.get_text(" ", strip=True)
                if len(title) < 15:
                    continue
                m = re.search(r"valor\.globo\.com/([a-z-]+)/", href)
                sec = heading or (m.group(1) if m and m.group(1) != "impresso" else "capa")
                by_url[href] = self.make(href, title, section=sec, prominence=weight,
                                         is_opinion=(sec == "opiniao"))
                n_new += 1
        log.info("impresso %s: %d já no RSS, %d adicionadas", day, n_hit, n_new)

    # --------------------------------------------------------------- texto integral
    def _fetch_bodies(self, articles, max_n: int):
        from .browser import LoggedBrowser, extract_text, has_profile
        if not has_profile():
            log.warning("Valor: sem perfil de navegador logado — texto integral só do RSS/impresso; "
                        "rode `python -m briefing login valor` uma vez")
            return articles
        pending = [a for a in articles if not a.body]
        top = sorted(pending, key=lambda a: a.prominence, reverse=True)[:max_n]
        if not top:
            return articles
        paywalled = 0
        with LoggedBrowser() as b:
            for a in top:
                try:
                    html = b.fetch(str(a.url))
                    data = extract_text(html, str(a.url))
                    text = data.get("text") or ""
                    if len(text) > 400:
                        a.body, a.word_count = text, len(text.split())
                    else:
                        paywalled += 1
                except Exception:
                    log.debug("falha ao buscar %s", a.url, exc_info=True)
        if top and paywalled / len(top) > 0.7:
            log.error("Valor: %d/%d páginas sem corpo — sessão da Conta Globo provavelmente expirou; "
                      "rode `python -m briefing login valor`", paywalled, len(top))
        return articles
