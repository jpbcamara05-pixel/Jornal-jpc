"""Curadoria: ~300 artigos → ~25 histórias ranqueadas.

1. dedup.py  : remove URL/título repetidos; agrupa a mesma história entre veículos
               (similaridade de título + embeddings leves) → clusters.
2. rank.py   : score = w1·prominence + w2·cross_coverage + w3·relevância_perfil (LLM
               barato em lote) + w4·recência; marca `seen_before` contra o SQLite.
3. corta por quota de tópico (settings.curation.per_topic_cards × 2, para dar
   escolha ao modelo principal).
"""

from __future__ import annotations

from ..models import Article, Story
from .dedup import cluster
from .rank import rank


def curate(articles: list[Article], settings: dict) -> list[Story]:
    stories = cluster(articles, settings)
    stories = rank(stories, settings)
    cfg = settings["curation"]
    top = stories[: cfg["max_articles_to_llm"]]
    # piso por veículo: garante que cada fonte chegue ao modelo com algumas histórias (o modelo decide o resto)
    floor = cfg.get("min_per_source", 0)
    if floor:
        chosen = {s.id for s in top}
        for src in {s.articles[0].source for s in stories}:
            have = [s for s in top if s.articles[0].source == src]
            extra = [s for s in stories if s.articles[0].source == src and s.id not in chosen][: max(0, floor - len(have))]
            top.extend(extra)
            chosen.update(s.id for s in extra)
    return sorted(top, key=lambda s: s.score, reverse=True)
