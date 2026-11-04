"""Histórias ranqueadas → Briefing (JSON do PDF)."""

from __future__ import annotations

from datetime import date

from ..models import Briefing, Story
from .client import load_prompt, parse


def _stories_block(stories: list[Story], max_body_chars: int = 2500) -> str:
    """Serializa as histórias para o prompt: id, tópico, score, fontes, texto truncado."""
    parts = []
    for s in stories:
        a = s.articles[0]
        others = [f"{x.source.value}: {x.url}" for x in s.articles[1:]]
        body = (a.body or a.summary or "")[:max_body_chars]
        parts.append(
            f"<story id='{s.id}' topic='{s.topic.value}' score='{s.score:.2f}' "
            f"cross='{s.cross_coverage}' seen_before='{s.seen_before}'>\n"
            f"FONTE: {a.source.value} | EDITORIA: {a.section} | PUBLICADO: {a.published_at}\n"
            f"URL: {a.url}\nTÍTULO: {a.title}\n"
            + (f"TAMBÉM EM: {'; '.join(others)}\n" if others else "")
            + f"TEXTO:\n{body}\n</story>"
        )
    return "\n\n".join(parts)


def _yesterday_block() -> str:
    """Resumo do briefing anterior (continuidade: 'como noticiamos ontem…', sem repetir)."""
    import json
    from datetime import timedelta

    from .. import config
    for back in (1, 2, 3):  # pula fim de semana
        f = config.OUTPUT_DIR / (date.today() - timedelta(days=back)).isoformat() / "briefing.json"
        if f.exists():
            b = json.loads(f.read_text(encoding="utf-8"))
            return f"Manchete: {b['headline']['title']}\n" + "\n".join(f"- {x}" for x in b["in_30_seconds"])
    return "(sem briefing anterior)"


def build_briefing(stories: list[Story], settings: dict) -> Briefing:
    llm = settings["llm"]
    system = load_prompt("system_editorial", reader_profile=settings["reader_profile"])
    user = load_prompt(
        "briefing",
        date=date.today().strftime("%d/%m/%Y"),
        quotas=settings["curation"]["per_topic_cards"],
        yesterday=_yesterday_block(),
        stories=_stories_block(stories),
    )
    return parse(Briefing, system=system, user=user, model=llm["model"],
                 effort=llm["effort"], max_tokens=llm["max_tokens"], label="briefing")
