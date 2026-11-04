"""Renderiza os entregáveis de exemplo (fixtures fictícias) para validar layout, voz e canal de entrega.

    .venv/bin/python scripts/preview_pdf.py           →  output/preview/*.pdf (celular + A4)
    .venv/bin/python scripts/preview_pdf.py --audio   →  output/preview/exemplo/ com 2 PDFs + 3 notas de voz
                                                        (é o conjunto que `python -m briefing test-delivery --sample` envia)
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from briefing.models import AudioScript, Briefing, DCMReport
from briefing.render.pdf import render_pdf

fx = ROOT / "tests" / "fixtures"
b = Briefing.model_validate(json.loads((fx / "briefing_exemplo.json").read_text(encoding="utf-8")))
d = DCMReport.model_validate(json.loads((fx / "dcm_exemplo.json").read_text(encoding="utf-8")))

if "--audio" in sys.argv:
    from dotenv import load_dotenv

    from briefing.render.audio import render_audio
    load_dotenv(ROOT / ".env")  # TTS_PROVIDER / voz
    out = ROOT / "output" / "preview" / "exemplo"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("briefing_exemplo.json", "dcm_exemplo.json", "audio_exemplo.json"):
        shutil.copy(fx / name, out / name.replace("_exemplo", "").replace("audio.json", "audio_scripts.json"))
    print(render_pdf(b, "briefing.html", out / "briefing.pdf"))
    print(render_pdf(d, "dcm.html", out / "termometro_dcm.pdf"))
    scripts = [AudioScript.model_validate(s) for s in json.loads((fx / "audio_exemplo.json").read_text(encoding="utf-8"))]
    for s in scripts:
        print(render_audio(s, out / f"audio_{s.channel.value}.ogg"))
else:
    out = ROOT / "output" / "preview"
    out.mkdir(parents=True, exist_ok=True)
    print(render_pdf(b, "briefing.html", out / "briefing_exemplo.pdf"))             # formato celular (padrão)
    print(render_pdf(d, "dcm.html", out / "termometro_dcm_exemplo.pdf"))
    print(render_pdf(b, "briefing.html", out / "briefing_exemplo_A4.pdf", "A4"))    # variante A4, 2 colunas
