"""Entrega no WhatsApp (ou Telegram como fallback). Interface única:

    send_text(to, text) · send_document(to, path, caption) · send_voice(to, path)

Provedor escolhido por DELIVERY_PROVIDER (ver docs/03-arquitetura.md § Entrega):
  whatsapp_waha      (padrão) self-hosted, proativo, grátis; chip reserva; risco de ban não-zero
  whatsapp_cloud     oficial Meta; PDF sai como template, mas ÁUDIO só dentro da janela de 24 h
                     (exige um toque seu no botão do template ou responder "ok" no dia anterior)
  whatsapp_evolution alternativa self-hosted (exige ativação de licença desde a v2.4)
  telegram           zero risco, zero custo, 10 linhas — rota de escape
  console            não envia: imprime o que enviaria (para testar o fluxo sem canal configurado)
Ordem e retries em settings.delivery.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from ..models import Briefing

log = logging.getLogger(__name__)


def _provider():
    name = os.environ.get("DELIVERY_PROVIDER", "whatsapp_waha")
    if name == "whatsapp_waha":
        from .whatsapp_waha import WahaProvider as P
    elif name == "whatsapp_evolution":
        from .whatsapp_evolution import EvolutionProvider as P
    elif name == "whatsapp_cloud":
        from .whatsapp_cloud import CloudProvider as P
    elif name == "telegram":
        from .telegram import TelegramProvider as P
    elif name == "console":
        from .console import ConsoleProvider as P
    else:
        raise ValueError(name)
    return P()


def opener_text(b: Briefing) -> str:
    bullets = "\n".join(f"• {x}" for x in b.in_30_seconds[:3])
    leia = "\n".join(f"→ {r.title} ({r.source_name}, {r.reading_minutes} min)" for r in b.read_today[:3])
    return (f"*Briefing {b.date.strftime('%d/%m')}* — {b.phrase_of_the_day}\n\n"
            f"*{b.headline.title}*\n{b.headline.summary}\n\n{bullets}\n\n*Leia hoje*\n{leia}")


def deliver(briefing: Briefing, outputs: dict[str, str], settings: dict) -> None:
    p = _provider()
    to = _recipient()
    plan = {
        "text": lambda: p.send_text(to, opener_text(briefing)),
        "briefing_pdf": lambda: p.send_document(to, outputs["briefing_pdf"], "Briefing do Dia"),
        "audio_mercado": lambda: p.send_voice(to, outputs["audio_mercado_empresas"]),
        "audio_economia": lambda: p.send_voice(to, outputs["audio_economia"]),
        "audio_politica": lambda: p.send_voice(to, outputs["audio_politica"]),
        "dcm_pdf": lambda: p.send_document(to, outputs["dcm_pdf"], "Termômetro DCM"),
    }
    for step in settings["delivery"]["order"]:
        for attempt in range(settings["delivery"]["retry_attempts"]):
            try:
                plan[step]()
                time.sleep(1.5)  # ordem garantida na conversa
                break
            except Exception:
                log.exception("falha enviando %s (tentativa %d)", step, attempt + 1)
                time.sleep(5 * (attempt + 1))


def _recipient() -> str:
    name = os.environ.get("DELIVERY_PROVIDER", "whatsapp_waha")
    if name == "telegram":
        return os.environ.get("TELEGRAM_CHAT_ID") or _missing("TELEGRAM_CHAT_ID")
    if name == "console":
        return os.environ.get("WHATSAPP_TO") or "(console)"
    return os.environ.get("WHATSAPP_TO") or _missing("WHATSAPP_TO")


def _missing(var: str) -> str:
    raise SystemExit(f"defina {var} no .env (ver .env.example)")


def ping() -> None:
    _provider().send_text(_recipient(), "✅ briefing: entrega configurada.")


def send_sample(settings: dict) -> dict[str, str]:
    """Envia o conjunto completo de exemplo (texto, 2 PDFs, 3 notas de voz) gerado a partir das fixtures
    em output/preview/exemplo/ — prova o canal de entrega de ponta a ponta sem chave da Anthropic."""
    import json

    from .. import config
    folder = config.OUTPUT_DIR / "preview" / "exemplo"
    if not (folder / "briefing.json").exists():
        raise SystemExit("gere o exemplo primeiro: python scripts/preview_pdf.py --audio")
    briefing = Briefing.model_validate(json.loads((folder / "briefing.json").read_text(encoding="utf-8")))
    outputs = {
        "briefing_pdf": str(folder / "briefing.pdf"),
        "dcm_pdf": str(folder / "termometro_dcm.pdf"),
        "audio_mercado_empresas": str(folder / "audio_mercado_empresas.ogg"),
        "audio_economia": str(folder / "audio_economia.ogg"),
        "audio_politica": str(folder / "audio_politica.ogg"),
    }
    missing = [k for k, v in outputs.items() if not Path(v).exists()]
    if missing:
        raise SystemExit(f"faltam {missing} em {folder}; rode: python scripts/preview_pdf.py --audio")
    deliver(briefing, outputs, settings)
    return outputs
