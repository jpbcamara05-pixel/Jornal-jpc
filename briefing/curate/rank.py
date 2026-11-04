"""Ranking das histórias."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from pydantic import BaseModel

from ..models import Story

log = logging.getLogger(__name__)


class RelevanceScores(BaseModel):
    scores: dict[str, float]  # story_id → 0..1


def rank(stories: list[Story], settings: dict) -> list[Story]:
    w = settings["curation"]["weights"]
    rel = _profile_relevance(stories, settings)
    from ..storage import db
    recent_ids = db.recent_story_ids(settings["dedup_window_days"])
    now = datetime.now(UTC)
    for s in stories:
        a = s.articles[0]
        age_h = (now - a.published_at).total_seconds() / 3600 if a.published_at else 12
        recency = max(0.0, 1 - age_h / 36)
        s.seen_before = s.id in recent_ids
        s.score = (w["prominence"] * a.prominence
                   + w["cross_coverage"] * min(s.cross_coverage - 1, 3) / 3
                   + w["profile_relevance"] * rel.get(s.id, 0.3)
                   + w["recency"] * recency)
        if s.seen_before:
            s.score *= 0.5
    return sorted(stories, key=lambda s: s.score, reverse=True)


def _profile_relevance(stories: list[Story], settings: dict) -> dict[str, float]:
    """Modelo barato pontua 0..1 a relevância de cada título+lead para o perfil do leitor.
    Lotes de ~60 histórias por chamada; só título e lead (barato)."""
    import os
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key or key.endswith("..."):
        log.warning("ANTHROPIC_API_KEY ausente: ranking sem relevância de perfil (neutro 0.3)")
        return {}
    from ..summarize.client import load_prompt, parse
    system = load_prompt("system_rank", reader_profile=settings["reader_profile"])
    out: dict[str, float] = {}
    for i in range(0, len(stories), 60):
        batch = stories[i:i + 60]
        lines = "\n".join(f"[{s.id}] ({s.articles[0].source.value}) {s.articles[0].title} — {(s.articles[0].summary or '')[:200]}"
                          for s in batch)
        res = parse(RelevanceScores, system=system, user=load_prompt("rank", items=lines),
                    model=settings["llm"]["bulk_model"], effort="low", label=f"rank_{i}")
        out.update(res.scores)
    return out
