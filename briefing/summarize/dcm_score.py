"""Score determinístico dos sinais DCM (0–100), a partir de config/dcm_signals.yaml → scoring.

    score = base(subtipo, 0–40) + urgência(data do evento, 0–20) + tamanho(R$, 0–15)
          + confiança da fonte(0–15) + corroboração(+5 por fonte extra, máx. 10) ± modificadores
    bandas: frio 0–19 · morno 20–39 · aquecendo 40–59 · quente 60–79 · fervendo 80–100
    decaimento: meia-vida de 7 dias úteis para notícias; eventos datados só decaem após a data.

Por que em código e não no LLM: reprodutível, auditável, ajustável no YAML sem reprompt.
O LLM extrai (subtipo, valor, data, tipo de fonte, confiança); o código pontua.
"""

from __future__ import annotations

import hashlib
import math
import re
from datetime import date

from ..models import DCMSignal, DCMSignalDraft, OpportunityType

BANDS = [(80, "fervendo"), (60, "quente"), (40, "aquecendo"), (20, "morno"), (0, "frio")]


def band_of(score: int) -> str:
    return next(label for floor, label in BANDS if score >= floor)


def _norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", t.lower().replace("s.a.", "").replace("s/a", ""))[:24]


def signal_id(d: DCMSignalDraft) -> str:
    return hashlib.sha1(f"{_norm(d.company)}|{d.opportunity.value}|{d.subtype}".encode()).hexdigest()[:10]


def score_signal(d: DCMSignalDraft, cfg: dict, today: date, corroborations: int = 0) -> DCMSignal:
    sc = cfg["scoring"]
    comp: dict[str, int] = {}

    # 1. base por subtipo (fallback: base da família)
    family = cfg["signals"][d.opportunity.value]
    comp["base"] = int(family.get("subtypes", {}).get(d.subtype, {}).get("base", family.get("base_default", 10)))

    # 2. urgência pela data do evento
    comp["urgencia"] = 0
    if d.event_date:
        days = (d.event_date - today).days
        for max_days, pts in sc["urgency_days"]:
            if days <= max_days:
                comp["urgencia"] = pts
                break

    # 3. tamanho
    comp["tamanho"] = 0
    if d.amount_brl:
        for min_amount, pts in sc["size_brl"]:
            if d.amount_brl >= min_amount:
                comp["tamanho"] = pts
                break

    # 4. confiança da fonte × confiança da extração
    conf_mult = sc["confidence_multiplier"][d.confidence.value]
    comp["fonte"] = round(sc["source_points"][d.source_type.value] * conf_mult)

    # 5. corroboração
    comp["corroboracao"] = min(sc["corroboration_points"] * corroborations, sc["corroboration_max"])

    # 6. modificadores
    mods = 0
    text = f"{d.evidence} {d.reading} {d.subtype}".lower()
    if any(sec in d.sector.lower() for sec in cfg.get("priority_sectors", [])):
        mods += sc["modifiers"]["priority_sector"]
    if re.search(r"refinanc|reembolso|resgate da|rolagem", text):
        mods += sc["modifiers"]["refinancing_destination"]
    if re.search(r"segunda convoca|reabertura|2ª convoca", text):
        mods += sc["modifiers"]["repeated_convocation"]
    if d.opportunity == OpportunityType.MACRO_REGULATORIO:
        mods += sc["modifiers"]["macro_penalty"]
    comp["modificadores"] = mods

    score = max(0, min(100, sum(comp.values())))
    return DCMSignal(**d.model_dump(), id=signal_id(d), score=score, band=band_of(score),
                     score_components=comp, corroborations=corroborations)


def dedup_and_score(drafts: list[DCMSignalDraft], cfg: dict, today: date) -> list[DCMSignal]:
    """Agrupa rascunhos pela chave (empresa, família, subtipo); cada fonte extra = corroboração."""
    groups: dict[str, list[DCMSignalDraft]] = {}
    for d in drafts:
        groups.setdefault(signal_id(d), []).append(d)
    out = []
    for items in groups.values():
        best = max(items, key=lambda x: (cfg["scoring"]["source_points"][x.source_type.value],
                                          cfg["scoring"]["confidence_multiplier"][x.confidence.value]))
        extra_sources = len({x.url for x in items}) - 1
        out.append(score_signal(best, cfg, today, corroborations=extra_sources))
    return sorted(out, key=lambda s: s.score, reverse=True)


def decayed(score: int, signal_day: date, today: date, event_date: date | None, half_life_days: int = 7) -> int:
    """Decaimento para o radar: notícias perdem metade a cada 7 dias úteis; eventos datados só após a data."""
    ref = max(signal_day, event_date) if event_date else signal_day
    days = max(0, (today - ref).days)
    business = days - 2 * (days // 7)
    return round(score * math.pow(0.5, business / half_life_days))


def day_temperature(signals: list[DCMSignal]) -> tuple[int, str]:
    """Temperatura do dia = 0,6 × maior score + 0,4 × média dos 3 maiores."""
    if not signals:
        return 0, "frio"
    top = sorted((s.score for s in signals), reverse=True)[:3]
    t = round(0.6 * top[0] + 0.4 * (sum(top) / len(top)))
    return t, band_of(t)
