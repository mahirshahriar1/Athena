"""SQLite persistence for research jobs and reports.

Lives next to ChromaDB in `data/athena.db`. Stdlib `sqlite3` only — no extra deps.
Used to persist results outside the LangGraph MemorySaver so reports survive restarts.
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from backend.core.config import settings

logger = logging.getLogger(__name__)

_DB_PATH = Path(settings.CHROMA_PERSIST_DIR).parent / "athena.db"
_lock = threading.Lock()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables on startup if missing."""
    with _lock, _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS research_jobs (
                id            TEXT PRIMARY KEY,
                company       TEXT NOT NULL,
                seed_url      TEXT,
                status        TEXT NOT NULL,
                plan_json     TEXT,
                final_report  TEXT,
                tokens_json   TEXT,
                kind          TEXT NOT NULL DEFAULT 'single',
                meta_json     TEXT,
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_research_jobs_created
                ON research_jobs(created_at DESC);
            """
        )
    logger.info(f"SQLite initialised at {_DB_PATH}")


def insert_job(
    job_id: str,
    company: str,
    seed_url: str | None,
    plan: list[str],
    kind: str = "single",
    meta: dict | None = None,
) -> None:
    now = _utcnow()
    with _lock, _connect() as conn:
        conn.execute(
            """
            INSERT INTO research_jobs
              (id, company, seed_url, status, plan_json, kind, meta_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              company   = excluded.company,
              seed_url  = excluded.seed_url,
              plan_json = excluded.plan_json,
              status    = excluded.status,
              kind      = excluded.kind,
              meta_json = excluded.meta_json,
              updated_at = excluded.updated_at
            """,
            (
                job_id,
                company,
                seed_url,
                "awaiting_approval",
                json.dumps(plan),
                kind,
                json.dumps(meta) if meta is not None else None,
                now,
                now,
            ),
        )


def update_status(job_id: str, status: str) -> None:
    with _lock, _connect() as conn:
        conn.execute(
            "UPDATE research_jobs SET status = ?, updated_at = ? WHERE id = ?",
            (status, _utcnow(), job_id),
        )


def update_plan(job_id: str, plan: list[str]) -> None:
    with _lock, _connect() as conn:
        conn.execute(
            "UPDATE research_jobs SET plan_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(plan), _utcnow(), job_id),
        )


def save_completion(
    job_id: str, final_report: str, tokens: dict | None = None
) -> None:
    with _lock, _connect() as conn:
        conn.execute(
            """
            UPDATE research_jobs
               SET final_report = ?, tokens_json = ?, status = 'completed', updated_at = ?
             WHERE id = ?
            """,
            (
                final_report,
                json.dumps(tokens) if tokens is not None else None,
                _utcnow(),
                job_id,
            ),
        )


def get_job(job_id: str) -> dict | None:
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM research_jobs WHERE id = ?", (job_id,)
        ).fetchone()
    if not row:
        return None
    return _row_to_dict(row)


def list_jobs(limit: int = 50) -> list[dict]:
    with _lock, _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, company, seed_url, status, kind, created_at, updated_at
              FROM research_jobs
             ORDER BY created_at DESC
             LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    if d.get("plan_json"):
        try:
            d["plan"] = json.loads(d["plan_json"])
        except json.JSONDecodeError:
            d["plan"] = []
    else:
        d["plan"] = []
    if d.get("tokens_json"):
        try:
            d["tokens"] = json.loads(d["tokens_json"])
        except json.JSONDecodeError:
            d["tokens"] = None
    else:
        d["tokens"] = None
    if d.get("meta_json"):
        try:
            d["meta"] = json.loads(d["meta_json"])
        except json.JSONDecodeError:
            d["meta"] = None
    else:
        d["meta"] = None
    d.pop("plan_json", None)
    d.pop("tokens_json", None)
    d.pop("meta_json", None)
    return d
