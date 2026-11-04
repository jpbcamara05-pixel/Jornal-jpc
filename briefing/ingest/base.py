from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import UTC, date, datetime

from ..models import Article, Market, Source


class Collector(ABC):
    name: str = "base"
    source: Source
    market: Market

    @abstractmethod
    def collect(self, settings: dict, day: date) -> list[Article]: ...

    def make(self, url: str, title: str, **kw) -> Article:
        return Article(
            id=hashlib.sha1(f"{self.source.value}|{url}".encode()).hexdigest()[:16],
            source=self.source, market=self.market, url=url, title=title,
            fetched_at=datetime.now(UTC), **kw,
        )
