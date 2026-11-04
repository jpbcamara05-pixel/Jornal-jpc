"""Artigos + avisos → DCMReport (Termômetro).

Três passos:
1. Triagem barata: regex por palavras-chave de config/dcm_signals.yaml → candidatos; o modelo
   pequeno extrai DCMSignalDraft em lote (subtipo, valor, data, tipo de fonte, evidência literal).
2. Código: dedup por (empresa, família, subtipo), corroboração, score 0–100 (dcm_score.py),
   temperatura do dia.
3. Consolidação (modelo principal): escolhe os 5 mais acionáveis, escreve a justificativa,
   lista avisos/editais, contexto de crédito e próximos eventos. O relatório é montado em código
   para que score e temperatura sejam sempre os calculados.
"""

from __future__ import annotations

import logging
from datetime import date

from pydantic import BaseModel

from .. import config
from ..models import Article, DCMReport, DCMReportDraft, DCMSignalDraft, Story
from .client import load_prompt, parse
from .dcm_score import day_temperature, dedup_and_score

log = logging.getLogger(__name__)


class SignalBatch(BaseModel):
    signals: list[DCMSignalDraft]


def _keyword_filter(articles: list[Article], taxonomy: dict) -> list[tuple[Article, list[str]]]:
    noise = [n.lower() for n in taxonomy.get("exclusions", [])]
    hits = []
    for a in articles:
        text = f"{a.title}\n{a.summary or ''}\n{a.body or ''}".lower()
        if a.source.value in ("cvm", "b3", "trustee", "valor_legais") and any(n in a.title.lower() for n in noise):
            continue  # "pagamento de juros", "relatório de proventos"… não são oportunidade
        matched = sorted({kw for fam in taxonomy["signals"].values()
                          for st in fam.get("subtypes", {}).values() for kw in st["keywords"] if kw.lower() in text})
        if matched:
            hits.append((a, matched))
    return hits


def build_dcm_report(articles: list[Article], stories: list[Story], settings: dict) -> DCMReport:
    llm = settings["llm"]
    today = date.today()
    taxonomy = config.load_yaml("dcm_signals.yaml")
    system = load_prompt("system_dcm", reader_profile=settings["reader_profile"],
                         taxonomy=taxonomy["prompt_summary"])

    # 1. extração em lotes com o modelo barato -----------------------------------
    candidates = _keyword_filter(articles, taxonomy)
    log.info("dcm: %d candidatos por palavra-chave", len(candidates))
    drafts: list[DCMSignalDraft] = []
    for i in range(0, len(candidates), 15):
        batch = candidates[i:i + 15]
        block = "\n\n".join(
            f"<doc url='{a.url}' source='{a.source.value}' section='{a.section}' keywords='{', '.join(k)}'>\n"
            f"{a.title}\n{(a.body or a.summary or '')[:3000]}\n</doc>" for a, k in batch)
        out = parse(SignalBatch, system=system, user=load_prompt("dcm_extract", docs=block),
                    model=llm["bulk_model"], effort="low", label=f"dcm_extract_{i}")
        drafts.extend(out.signals)

    # 2. dedup + score em código ----------------------------------------------------
    signals = dedup_and_score(drafts, taxonomy, today)
    temperature, label = day_temperature(signals)

    # 3. consolidação com o modelo principal ------------------------------------------
    from ..storage import db
    recent = db.recent_signals(days=7)
    draft = parse(DCMReportDraft, system=system,
                  user=load_prompt("dcm_report", date=today.strftime("%d/%m/%Y"), temperature=temperature, band=label,
                                   signals="\n".join(s.model_dump_json() for s in signals), recent="\n".join(recent)),
                  model=llm["model"], effort=llm["effort"], label="dcm_report")

    by_id = {s.id: s for s in signals}
    top = [by_id[i] for i in draft.top_signal_ids if i in by_id][:5]
    if not top:  # LLM não devolveu ids válidos → usa o ranking do score
        top = signals[:5]
    others = [s for s in signals if s not in top]
    report = DCMReport(date=today, temperature=temperature, temperature_label=label,
                       temperature_rationale=draft.temperature_rationale, top_signals=top, other_signals=others,
                       notices=draft.notices, credit_context=draft.credit_context, upcoming_events=draft.upcoming_events)
    db.save_signals(report)
    return report
