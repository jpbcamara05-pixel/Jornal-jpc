"""Briefing → 3 roteiros de áudio (mesmo conteúdo, escrito para ser ouvido)."""

from __future__ import annotations

from ..models import AudioChannel, AudioScript, Briefing, Story
from .client import load_prompt, parse

CHANNEL_SCOPE = {
    AudioChannel.MERCADO_EMPRESAS: ("mercado_empresas", "internacional"),
    AudioChannel.ECONOMIA: ("economia",),
    AudioChannel.POLITICA: ("politica",),
}


def build_audio_scripts(briefing: Briefing, stories: list[Story], settings: dict) -> list[AudioScript]:
    llm = settings["llm"]
    system = load_prompt("system_editorial", reader_profile=settings["reader_profile"])
    scripts = []
    for channel, sections in CHANNEL_SCOPE.items():
        cards = [c for sec in sections for c in getattr(briefing, sec)]
        if channel == AudioChannel.MERCADO_EMPRESAS:
            cards = [briefing.headline, *cards]
        cards_txt = "\n\n".join(
            f"- {c.title}\n  {c.summary}\n  Por que importa: {c.why_it_matters}\n  Fonte: {c.source_name}"
            for c in cards
        )
        user = load_prompt("audio_script", channel=channel.value, date=briefing.date.strftime("%A, %d de %B"),
                           cards=cards_txt, phrase=briefing.phrase_of_the_day)
        scripts.append(parse(AudioScript, system=system, user=user, model=llm["model"],
                             effort="medium", label=f"audio_{channel.value}"))
    return scripts
