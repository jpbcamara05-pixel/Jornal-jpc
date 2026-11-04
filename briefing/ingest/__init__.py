"""Coleta. Cada fonte implementa `Collector.collect(settings, day) -> list[Article]`.

Estratégia em camadas (da mais barata/robusta para a mais frágil):
  1. RSS/API oficial         → título, lead, URL, data, editoria (sempre funciona)
  2. Texto integral          → via navegador logado (Playwright, perfil persistente)
                               ou extrator (trafilatura) quando não há paywall
  3. Newsletters por IMAP    → "edição do dia" já curada pelo próprio veículo
                               (Valor, Brazil Journal, FirstFT, The Morning, 10-Point)
  4. Capa / edição impressa  → só para marcar `prominence` (o que o jornal escolheu destacar)

As URLs dos feeds ficam em config/sources.yaml.
"""

from __future__ import annotations

import logging
from datetime import date

from ..models import Article
from .base import Collector

log = logging.getLogger(__name__)


def collect_all(settings: dict, day: date) -> list[Article]:
    from .braziljournal import BrazilJournalCollector
    from .dcm_sources import DCMNoticesCollector
    from .intl import FTCollector, NYTCollector, WSJCollector
    from .newsletters import NewsletterCollector
    from .valor import ValorCollector

    collectors: list[Collector] = [
        ValorCollector(), BrazilJournalCollector(),
        FTCollector(), NYTCollector(), WSJCollector(),
        NewsletterCollector(), DCMNoticesCollector(),
    ]
    articles: list[Article] = []
    for c in collectors:
        try:
            got = c.collect(settings, day)
            log.info("%s: %d artigos", c.name, len(got))
            articles.extend(got)
        except Exception:  # uma fonte fora do ar não derruba o briefing
            log.exception("falha em %s — seguindo sem essa fonte", c.name)

    from ..storage import db
    db.upsert_articles(articles)
    return articles
