"""Orquestração do dia: coleta → curadoria → síntese → render → entrega.

Cada etapa é idempotente e grava seu resultado em disco (output/YYYY-MM-DD/),
então uma falha no meio permite retomar com `--from <etapa>` sem recoletar
ou pagar o LLM de novo.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

from . import config
from .models import Article, AudioScript, Briefing, DCMReport, RunResult, Story

log = logging.getLogger(__name__)

STAGES = ["ingest", "curate", "summarize", "render", "deliver"]


def run(
    day: date | None = None,
    start_from: str = "ingest",
    dry_run: bool = False,
    until: str = "deliver",
) -> RunResult:
    settings = config.load_settings()
    day = day or date.today()
    out_dir = config.OUTPUT_DIR / day.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    result = RunResult(date=day, started_at=datetime.now())

    stages = STAGES[STAGES.index(start_from): STAGES.index(until) + 1]
    log.info("run %s | etapas: %s", day, stages)

    # 1. Coleta -------------------------------------------------------------
    if "ingest" in stages:
        from .ingest import collect_all
        articles = collect_all(settings, day)
        result.articles_collected = len(articles)
        _save(out_dir / "articles.json", articles)
    elif "curate" in stages or "summarize" in stages:
        articles = _load(out_dir / "articles.json", Article)

    # 2. Curadoria ----------------------------------------------------------
    if "curate" in stages:
        from .curate import curate
        stories = curate(articles, settings)
        result.stories_ranked = len(stories)
        _save(out_dir / "stories.json", stories)
    elif "summarize" in stages:
        stories = _load(out_dir / "stories.json", Story)

    # 3. Síntese (LLM) ------------------------------------------------------
    if "summarize" in stages:
        from .summarize import build_audio_scripts, build_briefing, build_dcm_report
        briefing = build_briefing(stories, settings)
        scripts = build_audio_scripts(briefing, stories, settings)
        dcm = build_dcm_report(articles, stories, settings)
        _save(out_dir / "briefing.json", briefing)
        _save(out_dir / "audio_scripts.json", scripts)
        _save(out_dir / "dcm.json", dcm)
    elif "render" in stages or "deliver" in stages:
        briefing = _load(out_dir / "briefing.json", Briefing)
        scripts = _load(out_dir / "audio_scripts.json", AudioScript)
        dcm = _load(out_dir / "dcm.json", DCMReport)

    # 4. Render -------------------------------------------------------------
    if "render" in stages:
        from .render import render_audio, render_pdf
        result.outputs = {}
        ps = settings["pdf"]["page_size"]
        result.outputs["briefing_pdf"] = render_pdf(briefing, "briefing.html", out_dir / "briefing.pdf", ps)
        result.outputs["dcm_pdf"] = render_pdf(dcm, "dcm.html", out_dir / "termometro_dcm.pdf", ps)
        for s in scripts:
            result.outputs[f"audio_{s.channel.value}"] = render_audio(s, out_dir / f"audio_{s.channel.value}.ogg")

    # 5. Entrega ------------------------------------------------------------
    if "deliver" in stages and not dry_run:
        from .deliver import deliver
        if not result.outputs:  # retomada direta em `deliver`: reaproveita arquivos do dia
            result.outputs = _existing_outputs(out_dir, scripts)
        deliver(briefing, result.outputs, settings)
        result.delivered = True

    result.finished_at = datetime.now()
    _save(out_dir / "run.json", result)
    return result


def _save(path, obj) -> None:
    import json

    from pydantic import BaseModel

    def enc(o):
        if isinstance(o, BaseModel):
            return o.model_dump(mode="json")
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        raise TypeError(type(o))

    path.write_text(json.dumps(obj, default=enc, ensure_ascii=False, indent=2), encoding="utf-8")


def _load(path, model):
    """Relê o JSON de uma etapa anterior já validado nos modelos pydantic."""
    import json
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [model.model_validate(x) for x in raw]
    return model.model_validate(raw)


def _existing_outputs(out_dir, scripts) -> dict:
    outs = {"briefing_pdf": out_dir / "briefing.pdf", "dcm_pdf": out_dir / "termometro_dcm.pdf"}
    for s in scripts:
        outs[f"audio_{s.channel.value}"] = out_dir / f"audio_{s.channel.value}.ogg"
    return {k: str(v) for k, v in outs.items() if v.exists()}
