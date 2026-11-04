"""HTML/CSS → PDF com WeasyPrint.

Por que WeasyPrint: layout em cards com CSS normal (grid/flex), fontes próprias,
quebra de página controlada (`break-inside: avoid`), sem precisar de navegador.
Alternativa drop-in: Playwright `page.pdf()` se algum CSS moderno faltar.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

TEMPLATES = Path(__file__).parent / "templates"

# "phone": uma coluna, 420×760 pt (legível no WhatsApp sem zoom). "A4": duas colunas.
PAGE_SIZES = {"phone": {"css": "420pt 760pt", "cls": "phone"}, "A4": {"css": "A4", "cls": "a4"}}


def render_pdf(data: BaseModel | dict, template: str, out: Path, page_size: str = "phone") -> str:
    from weasyprint import HTML
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
    env.filters["br_date"] = _br_date
    ctx = data.model_dump(mode="json") if isinstance(data, BaseModel) else data
    html = env.get_template(template).render(**ctx, _raw=ctx, _page=PAGE_SIZES[page_size])
    (out.with_suffix(".html")).write_text(html, encoding="utf-8")  # útil para depurar o layout
    HTML(string=html, base_url=str(TEMPLATES)).write_pdf(str(out))
    return str(out)


def _br_date(iso: str) -> str:
    from datetime import date
    d = date.fromisoformat(iso)
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]
    dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
    return f"{dias[d.weekday()]}, {d.day} de {meses[d.month - 1]} de {d.year}"
