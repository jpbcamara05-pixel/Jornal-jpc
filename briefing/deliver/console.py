"""Provedor "console": não envia nada, só imprime o que seria enviado (ordem, tamanho dos arquivos).

Serve para validar o fluxo de entrega sem WhatsApp/Telegram configurados:
    DELIVERY_PROVIDER=console python -m briefing test-delivery --sample
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)


class ConsoleProvider:
    def send_text(self, to, text):
        log.info("→ %s | TEXTO (%d chars):\n%s", to, len(text), text)

    def send_document(self, to, path, caption=""):
        p = Path(path)
        log.info("→ %s | PDF %s (%.0f KB) legenda=%r", to, p.name, p.stat().st_size / 1024, caption)

    def send_voice(self, to, path):
        p = Path(path)
        log.info("→ %s | NOTA DE VOZ %s (%.0f KB)", to, p.name, p.stat().st_size / 1024)
