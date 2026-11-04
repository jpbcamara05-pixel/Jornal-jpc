"""FT, NYT, WSJ — mercado internacional.

Camada 1 (sempre): RSS oficial (FT, WSJ) e NYT Top Stories API (chave gratuita).
Camada 2 (opcional, se houver assinatura): texto integral via LoggedBrowser,
            limitado aos ~10 artigos mais proeminentes por veículo.
Camada 3 (recomendada): newsletters FirstFT / The Morning / The 10-Point via IMAP
            — já são a curadoria do próprio jornal e chegam por e-mail sem anti-bot.
"""

from __future__ import annotations

import os
from datetime import date

import requests

from ..models import Market, Source
from .base import Collector
from .rss import read_feed


class _RSSIntl(Collector):
    market = Market.INTERNATIONAL
    key: str

    def collect(self, settings: dict, day: date) -> list:
        from .. import config
        cfg = config.load_yaml("sources.yaml")[self.key]
        out = []
        for section, url in cfg["feeds"].items():
            for it in read_feed(url, settings["lookback_hours"]):
                out.append(self.make(it["url"], it["title"], summary=it["summary"], section=section,
                                     published_at=it["published_at"], prominence=cfg.get("section_weights", {}).get(section, 0.3)))
        return out


class FTCollector(_RSSIntl):
    name, key, source = "ft", "ft", Source.FT


class WSJCollector(_RSSIntl):
    name, key, source = "wsj", "wsj", Source.WSJ


class NYTCollector(Collector):
    name, source, market = "nyt", Source.NYT, Market.INTERNATIONAL

    def collect(self, settings: dict, day: date) -> list:
        key = os.environ.get("NYT_API_KEY")
        if not key:
            return []
        out = []
        for section, weight in (("business", 0.6), ("world", 0.4), ("home", 0.8)):
            r = requests.get(f"https://api.nytimes.com/svc/topstories/v2/{section}.json",
                             params={"api-key": key}, timeout=30)
            r.raise_for_status()
            for it in r.json().get("results", []):
                if not it.get("url"):
                    continue
                out.append(self.make(it["url"], it["title"], summary=it.get("abstract"), section=it.get("section"),
                                     prominence=weight, raw={"des_facet": it.get("des_facet", [])}))
        return out
