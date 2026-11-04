"""Evolution API (self-hosted, Docker) — WhatsApp via Baileys, sem Meta Business.

Endpoints usados (v2): /message/sendText, /message/sendMedia (document),
/message/sendWhatsAppAudio (nota de voz PTT). Docs: https://doc.evolution-api.com
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import requests


class EvolutionProvider:
    def __init__(self):
        self.url = os.environ["EVOLUTION_API_URL"].rstrip("/")
        self.inst = os.environ["EVOLUTION_INSTANCE"]
        self.h = {"apikey": os.environ["EVOLUTION_API_KEY"], "Content-Type": "application/json"}

    def _post(self, path: str, body: dict):
        r = requests.post(f"{self.url}/{path}/{self.inst}", json=body, headers=self.h, timeout=120)
        r.raise_for_status()
        return r.json()

    def send_text(self, to: str, text: str):
        return self._post("message/sendText", {"number": to, "text": text})

    def send_document(self, to: str, path: str, caption: str = ""):
        p = Path(path)
        return self._post("message/sendMedia", {
            "number": to, "mediatype": "document", "mimetype": "application/pdf",
            "caption": caption, "fileName": p.name, "media": base64.b64encode(p.read_bytes()).decode(),
        })

    def send_voice(self, to: str, path: str):
        return self._post("message/sendWhatsAppAudio", {
            "number": to, "audio": base64.b64encode(Path(path).read_bytes()).decode(), "encoding": True,
        })
