"""WAHA (devlikeapro/waha) — WhatsApp HTTP API self-hosted em Docker, gratuito desde a 2026.6.

Por que é o padrão deste projeto: envia PDF e nota de voz de forma PROATIVA (sem a
janela de 24 h da API oficial), um container só, sem Chromium (engine NOWEB/GOWS).
Risco: é uma sessão não oficial do WhatsApp → use um chip reserva, nunca o número
principal. Docs: https://waha.devlike.pro/docs/how-to/send-messages/

    docker run -d --name waha -p 3000:3000 -v waha_sessions:/app/.sessions \
      -e WHATSAPP_DEFAULT_ENGINE=NOWEB -e WAHA_API_KEY=... devlikeapro/waha
    → abrir http://localhost:3000 (Swagger), iniciar sessão 'default', ler o QR com o chip reserva.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import requests


class WahaProvider:
    def __init__(self):
        self.url = os.environ.get("WAHA_URL", "http://localhost:3000").rstrip("/")
        self.session = os.environ.get("WAHA_SESSION", "default")
        self.h = {"X-Api-Key": os.environ.get("WAHA_API_KEY", ""), "Content-Type": "application/json"}

    @staticmethod
    def _chat(to: str) -> str:
        return to if "@" in to else f"{to}@c.us"

    def _post(self, path: str, body: dict):
        r = requests.post(f"{self.url}/api/{path}", json={"session": self.session, **body}, headers=self.h, timeout=180)
        r.raise_for_status()
        return r.json()

    def send_text(self, to: str, text: str):
        return self._post("sendText", {"chatId": self._chat(to), "text": text})

    def send_document(self, to: str, path: str, caption: str = ""):
        p = Path(path)
        return self._post("sendFile", {"chatId": self._chat(to), "caption": caption, "file": {
            "mimetype": "application/pdf", "filename": p.name, "data": base64.b64encode(p.read_bytes()).decode()}})

    def send_voice(self, to: str, path: str):
        p = Path(path)
        # convert=True deixa o WAHA transcodificar se não for OGG/Opus; já mandamos Opus, mas é seguro.
        return self._post("sendVoice", {"chatId": self._chat(to), "convert": True, "file": {
            "mimetype": "audio/ogg; codecs=opus", "filename": p.name, "data": base64.b64encode(p.read_bytes()).decode()}})
