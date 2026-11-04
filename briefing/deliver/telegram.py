"""Telegram Bot API — fallback trivial (sem ban, sem Meta). sendVoice toca como nota de voz."""

from __future__ import annotations

import os

import requests


class TelegramProvider:
    def __init__(self):
        self.base = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}"

    def send_text(self, to, text):
        return requests.post(f"{self.base}/sendMessage", json={"chat_id": to, "text": text, "parse_mode": "Markdown"}, timeout=60).json()

    def send_document(self, to, path, caption=""):
        with open(path, "rb") as f:
            return requests.post(f"{self.base}/sendDocument", data={"chat_id": to, "caption": caption}, files={"document": f}, timeout=120).json()

    def send_voice(self, to, path):
        with open(path, "rb") as f:
            return requests.post(f"{self.base}/sendVoice", data={"chat_id": to}, files={"voice": f}, timeout=120).json()
