"""Brazil Journal — sem paywall; RSS + trafilatura direto (sem navegador)."""

from __future__ import annotations

from datetime import date

from ..models import Market, Source
from .base import Collector
from .rss import read_feed


class BrazilJournalCollector(Collector):
    name = "brazil_journal"
    source = Source.BRAZIL_JOURNAL
    market = Market.LOCAL

    def collect(self, settings: dict, day: date) -> list:
        import trafilatura

        from .. import config
        cfg = config.load_yaml("sources.yaml")["brazil_journal"]
        out = []
        for section, url in cfg["feeds"].items():
            for it in read_feed(url, settings["lookback_hours"]):
                a = self.make(it["url"], it["title"], summary=it["summary"], section=section,
                              published_at=it["published_at"], prominence=0.5)
                html = trafilatura.fetch_url(it["url"])
                a.body = trafilatura.extract(html) if html else it.get("content")
                out.append(a)
        return out
