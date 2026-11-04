"""Render: JSON → PDF (Jinja2 + HTML/CSS → WeasyPrint) e roteiro → áudio (TTS → ffmpeg → OGG/Opus)."""

from .audio import render_audio
from .pdf import render_pdf

__all__ = ["render_audio", "render_pdf"]
