"""Meta WhatsApp Cloud API (oficial). Requer app Meta + número de negócio.

Fluxo: upload de mídia (/{phone_id}/media) → envio (/{phone_id}/messages) com
type=document|audio. Áudio OGG/Opus é tocado como nota de voz.
"""

from __future__ import annotations

import os
from pathlib import Path

import requests

GRAPH = "https://graph.facebook.com/v21.0"


class CloudProvider:
    def __init__(self):
        self.token = os.environ["WA_CLOUD_TOKEN"]
        self.phone_id = os.environ["WA_CLOUD_PHONE_NUMBER_ID"]
        self.h = {"Authorization": f"Bearer {self.token}"}

    def _upload(self, path: str, mime: str) -> str:
        with open(path, "rb") as f:
            r = requests.post(f"{GRAPH}/{self.phone_id}/media", headers=self.h,
                              data={"messaging_product": "whatsapp", "type": mime},
                              files={"file": (Path(path).name, f, mime)}, timeout=120)
        r.raise_for_status()
        return r.json()["id"]

    def _send(self, body: dict):
        r = requests.post(f"{GRAPH}/{self.phone_id}/messages", headers=self.h,
                          json={"messaging_product": "whatsapp", **body}, timeout=60)
        r.raise_for_status()
        return r.json()

    def send_text(self, to, text):
        return self._send({"to": to, "type": "text", "text": {"body": text}})

    def send_document(self, to, path, caption=""):
        mid = self._upload(path, "application/pdf")
        return self._send({"to": to, "type": "document",
                           "document": {"id": mid, "caption": caption, "filename": Path(path).name}})

    def send_voice(self, to, path):
        mid = self._upload(path, "audio/ogg")
        return self._send({"to": to, "type": "audio", "audio": {"id": mid}})
