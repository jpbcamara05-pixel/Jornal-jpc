"""Renderiza os PDFs de exemplo (fixtures fictícias) para validar o layout.

    .venv/bin/python scripts/preview_pdf.py   →  output/preview/*.pdf
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from briefing.models import Briefing, DCMReport
from briefing.render.pdf import render_pdf

out = ROOT / "output" / "preview"
out.mkdir(parents=True, exist_ok=True)
fx = ROOT / "tests" / "fixtures"

b = Briefing.model_validate(json.loads((fx / "briefing_exemplo.json").read_text(encoding="utf-8")))
d = DCMReport.model_validate(json.loads((fx / "dcm_exemplo.json").read_text(encoding="utf-8")))
print(render_pdf(b, "briefing.html", out / "briefing_exemplo.pdf"))             # formato celular (padrão)
print(render_pdf(d, "dcm.html", out / "termometro_dcm_exemplo.pdf"))
print(render_pdf(b, "briefing.html", out / "briefing_exemplo_A4.pdf", "A4"))    # variante A4, 2 colunas
