"""Síntese com LLM (Claude). Três saídas estruturadas a partir das histórias ranqueadas:

- build_briefing      → Briefing   (JSON que alimenta o PDF e a mensagem de texto)
- build_audio_scripts → [AudioScript x3]  (roteiros derivados do MESMO Briefing)
- build_dcm_report    → DCMReport  (sinais + avisos → Termômetro DCM)

Padrão em todas: `client.messages.parse(..., output_format=Modelo)` devolve o
pydantic já validado; prompts ficam em summarize/prompts/*.md e são
cacheados (cache_control) porque são o prefixo estável de toda chamada.
"""

from .audio_script import build_audio_scripts
from .briefing import build_briefing
from .dcm import build_dcm_report

__all__ = ["build_audio_scripts", "build_briefing", "build_dcm_report"]
