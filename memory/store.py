import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from config.settings import settings

# Relative paths resolve against the repo root; an absolute MEMORY_DB_PATH
# overrides that entirely (pathlib drops the left side when the right side is
# absolute). That's the hook for pointing the DB at mounted persistent storage
# -- e.g. MEMORY_DB_PATH=/data/memory.db on a Space with a persistent disk,
# since the default location is wiped on every container restart.
_DB_PATH = Path(__file__).resolve().parents[1] / settings.memory_db_path


def _connect() -> sqlite3.Connection:
    # Schema creation runs on every connect (not just once at import time):
    # CREATE TABLE IF NOT EXISTS is cheap, and this way the tables always
    # exist even if the underlying DB file is missing/fresh -- e.g. a new
    # Docker volume on first boot -- rather than only on first import.
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            query TEXT NOT NULL,
            intent_type TEXT,
            sku TEXT,
            criticality_tier TEXT,
            supplier_id TEXT,
            response_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            query TEXT NOT NULL,
            intent_type TEXT,
            sku TEXT,
            criticality_tier TEXT,
            supplier_id TEXT,
            instruction TEXT NOT NULL
        )
        """
    )
    conn.commit()


def save_turn(
    session_id: str,
    query: str,
    intent_type: Optional[str],
    sku: Optional[str],
    criticality_tier: Optional[str],
    supplier_id: Optional[str],
    response_json: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO turns
                (session_id, timestamp, query, intent_type, sku, criticality_tier, supplier_id, response_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                datetime.now(timezone.utc).isoformat(),
                query,
                intent_type,
                sku,
                criticality_tier,
                supplier_id,
                response_json,
            ),
        )


def load_recent_turns(session_id: str, limit: int = 5) -> List[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM turns
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def save_feedback(
    session_id: str,
    query: str,
    intent_type: Optional[str],
    sku: Optional[str],
    criticality_tier: Optional[str],
    supplier_id: Optional[str],
    instruction: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO feedback
                (session_id, timestamp, query, intent_type, sku, criticality_tier, supplier_id, instruction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                datetime.now(timezone.utc).isoformat(),
                query,
                intent_type,
                sku,
                criticality_tier,
                supplier_id,
                instruction,
            ),
        )


def load_relevant_feedback(
    session_id: str,
    intent_type: Optional[str] = None,
    sku: Optional[str] = None,
    criticality_tier: Optional[str] = None,
    supplier_id: Optional[str] = None,
) -> List[dict]:
    # Decision #6: match on the SITUATION (any shared entity -- sku, tier,
    # supplier), not on exact query text. Falls back to matching on intent
    # category only if no specific entity is available to match on.
    conditions = ["session_id = ?"]
    params: list = [session_id]

    entity_conditions = []
    for column, value in (("sku", sku), ("criticality_tier", criticality_tier), ("supplier_id", supplier_id)):
        if value:
            entity_conditions.append(f"{column} = ?")
            params.append(value)

    if entity_conditions:
        conditions.append("(" + " OR ".join(entity_conditions) + ")")
    elif intent_type:
        conditions.append("intent_type = ?")
        params.append(intent_type)

    sql = f"SELECT * FROM feedback WHERE {' AND '.join(conditions)} ORDER BY id DESC"
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]
