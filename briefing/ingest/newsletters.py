"""Newsletters por e-mail (IMAP) → artigos já curados pelo veículo.

Por que: a newsletter matinal É a seleção do editor (Valor, Brazil Journal,
FirstFT, The Morning, The 10-Point). Chega sem anti-bot, sem paywall, com links.
Remetentes/assuntos em config/sources.yaml → newsletters.
"""

from __future__ import annotations

import email
import imaplib
import os
from datetime import date, timedelta

from ..models import Market, Source
from .base import Collector


class NewsletterCollector(Collector):
    name = "newsletters"
    source = Source.VALOR  # sobrescrito por item
    market = Market.LOCAL

    def collect(self, settings: dict, day: date) -> list:
        user, pwd = os.environ.get("IMAP_USER"), os.environ.get("IMAP_PASSWORD")
        if not (user and pwd):
            return []
        from .. import config
        cfg = config.load_yaml("sources.yaml")["newsletters"]
        since = (day - timedelta(days=1)).strftime("%d-%b-%Y")
        out = []
        with imaplib.IMAP4_SSL(os.environ.get("IMAP_HOST", "imap.gmail.com")) as m:
            m.login(user, pwd)
            m.select("INBOX")
            for nl in cfg:
                _, data = m.search(None, f'(FROM "{nl["from"]}" SINCE {since})')
                for num in data[0].split():
                    _, msg_data = m.fetch(num, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    html = _html_part(msg)
                    out.extend(self._links_to_articles(html, nl))
        return out

    def _links_to_articles(self, html: str, nl: dict) -> list:
        """TODO: extrair (título, link) dos blocos da newsletter; prominence alta (0.8)."""
        return []


def _html_part(msg) -> str:
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "ignore")
    return ""
