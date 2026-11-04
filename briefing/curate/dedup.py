"""Dedup + clustering de artigos em histórias."""

from __future__ import annotations

import hashlib
import re

from rapidfuzz import fuzz

from ..models import Article, Source, Story, Topic

# Fontes estruturadas do Termômetro: não viram "histórias" do briefing (vão direto para summarize/dcm.py)
DCM_SOURCES = {Source.CVM, Source.B3, Source.ANBIMA, Source.TRUSTEE, Source.VALOR_LEGAIS}

SECTION_TOPIC = {
    "empresas": Topic.MERCADO_EMPRESAS, "financas": Topic.MERCADO_EMPRESAS, "mercados": Topic.MERCADO_EMPRESAS,
    "business": Topic.MERCADO_EMPRESAS, "agronegocios": Topic.MERCADO_EMPRESAS, "agro": Topic.MERCADO_EMPRESAS,
    "valor-investe": Topic.MERCADO_EMPRESAS, "valor_investe": Topic.MERCADO_EMPRESAS, "pipeline": Topic.MERCADO_EMPRESAS,
    "brasil": Topic.ECONOMIA, "economia": Topic.ECONOMIA, "economy": Topic.ECONOMIA,
    "politica": Topic.POLITICA, "legislacao": Topic.POLITICA, "politics": Topic.POLITICA,
    "mundo": Topic.INTERNACIONAL, "world": Topic.INTERNACIONAL,
    "agd": Topic.DCM, "fato_relevante": Topic.DCM, "inicio_oferta": Topic.DCM,
}
# Editorias de feed que não dizem o assunto (capa, impresso…): a URL diz — valor.globo.com/<editoria>/...
_URL_SECTION = re.compile(r"https?://(?:valor|valorinveste|valorinternational)\.globo\.com/([a-z-]+)/")


def topic_of(a: Article) -> Topic:
    if a.market.value == "intl":
        return Topic.INTERNACIONAL
    sec = (a.section or "").lower()
    t = SECTION_TOPIC.get(sec)
    if t is None:
        m = _URL_SECTION.search(str(a.url))
        if m:
            t = SECTION_TOPIC.get(m.group(1))
    return t or Topic.OUTROS


def _norm(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", t.lower())


def cluster(articles: list[Article], settings: dict, threshold: int = 82) -> list[Story]:
    """Agrupa por similaridade de título (rapidfuzz token_set_ratio).
    TODO fase 2: embeddings (ex.: sentence-transformers multilingual) para pegar
    a mesma história com títulos muito diferentes entre PT e EN."""
    seen_urls: set[str] = set()
    clusters: list[list[Article]] = []
    news = [a for a in articles if a.source not in DCM_SOURCES]
    for a in sorted(news, key=lambda x: x.prominence, reverse=True):
        if str(a.url) in seen_urls:
            continue
        seen_urls.add(str(a.url))
        for c in clusters:
            if fuzz.token_set_ratio(_norm(a.title), _norm(c[0].title)) >= threshold:
                c.append(a)
                break
        else:
            clusters.append([a])

    stories = []
    for c in clusters:
        lead = c[0]
        topic = topic_of(lead)
        stories.append(Story(
            id=hashlib.sha1(lead.id.encode()).hexdigest()[:10], topic=topic, articles=c,
            score=0.0, cross_coverage=len({x.source for x in c}),
        ))
    return stories
