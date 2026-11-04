"""Leitura genérica de feeds RSS/Atom com feedparser + janela de tempo."""

from __future__ import annotations

import re
from calendar import timegm
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser

_TRACKING = re.compile(r"^(utm_|syn-|fbclid|gclid|ref$|cmpid|ocid)")


def read_feed(url: str, lookback_hours: int = 26) -> list[dict]:
    feed = feedparser.parse(url)
    cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)
    items = []
    for e in feed.entries:
        ts = e.get("published_parsed") or e.get("updated_parsed")
        # *_parsed já vem em UTC; timegm (não mktime) evita o deslocamento do fuso local
        published = datetime.fromtimestamp(timegm(ts), tz=UTC) if ts else None
        if published and published < cutoff:
            continue
        items.append({
            "url": clean_url(e.get("link")), "title": e.get("title", "").strip(),
            "summary": _clean(e.get("summary", "")), "published_at": published,
            "authors": [a.get("name") for a in e.get("authors", []) if a.get("name")],
            "tags": [t.get("term") for t in e.get("tags", [])],
            "content": _clean(e["content"][0]["value"]) if e.get("content") else None,
        })
    return items


def clean_url(url: str | None) -> str | None:
    """Remove parâmetros de rastreio (utm_*, syn-*, …) para que a mesma matéria tenha a mesma URL."""
    if not url:
        return url
    parts = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _TRACKING.match(k)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), ""))


def _clean(html: str) -> str:
    from bs4 import BeautifulSoup
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)
