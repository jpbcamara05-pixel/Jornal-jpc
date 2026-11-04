"""SQLite local: histórico de artigos (dedup entre dias), histórias enviadas, sinais DCM (radar)."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from .. import config

DB_PATH = config.DATA_DIR / "briefing.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
  id TEXT PRIMARY KEY, source TEXT, url TEXT, title TEXT, section TEXT,
  published_at TEXT, fetched_at TEXT, prominence REAL, has_body INTEGER
);
CREATE TABLE IF NOT EXISTS stories_sent (
  story_id TEXT, day TEXT, topic TEXT, title TEXT, PRIMARY KEY (story_id, day)
);
CREATE TABLE IF NOT EXISTS dcm_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT, signal_id TEXT, company TEXT, opportunity TEXT, subtype TEXT,
  score INTEGER, band TEXT, confidence TEXT, status TEXT DEFAULT 'novo', payload TEXT
);
"""


def _conn() -> sqlite3.Connection:
    config.DATA_DIR.mkdir(exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.executescript(SCHEMA)
    return c


def upsert_articles(articles) -> None:
    with _conn() as c:
        c.executemany(
            "INSERT OR REPLACE INTO articles VALUES (?,?,?,?,?,?,?,?,?)",
            [(a.id, a.source.value, str(a.url), a.title, a.section,
              a.published_at.isoformat() if a.published_at else None, a.fetched_at.isoformat(),
              a.prominence, int(bool(a.body))) for a in articles],
        )


def recent_story_ids(days: int) -> set[str]:
    since = (date.today() - timedelta(days=days)).isoformat()
    with _conn() as c:
        return {r[0] for r in c.execute("SELECT story_id FROM stories_sent WHERE day >= ?", (since,))}


def save_signals(report) -> None:
    with _conn() as c:
        c.executemany(
            "INSERT INTO dcm_signals (day, signal_id, company, opportunity, subtype, score, band, confidence, payload) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            [(report.date.isoformat(), s.id, s.company, s.opportunity.value, s.subtype, s.score, s.band,
              s.confidence.value, s.model_dump_json()) for s in [*report.top_signals, *report.other_signals]],
        )


def recent_signals(days: int = 7) -> list[str]:
    since = (date.today() - timedelta(days=days)).isoformat()
    with _conn() as c:
        return [f"[{d}] {p}" for d, p in c.execute(
            "SELECT day, payload FROM dcm_signals WHERE day >= ? AND day < ? ORDER BY score DESC",
            (since, date.today().isoformat()))]
