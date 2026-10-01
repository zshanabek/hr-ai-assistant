"""
AI Assistant — SQLite database.

Stores Telegram session tokens and conversation history per chat_id.
Replaces the in-memory _sessions and _histories dicts so state survives restarts.
"""

import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).parent / "ai_assistant.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS telegram_sessions (
            chat_id       INTEGER PRIMARY KEY,
            session_token TEXT NOT NULL,
            employee_id   TEXT,
            created_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversation_history (
            chat_id INTEGER PRIMARY KEY,
            history TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def get_session(chat_id: int) -> tuple[str, str] | tuple[None, None]:
    """Returns (session_token, employee_id) or (None, None)."""
    conn = get_conn()
    row = conn.execute(
        "SELECT session_token, employee_id FROM telegram_sessions WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    conn.close()
    if row:
        return row["session_token"], row["employee_id"]
    return None, None


def save_session(chat_id: int, session_token: str, employee_id: str | None = None) -> None:
    from datetime import datetime, timezone
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO telegram_sessions VALUES (?, ?, ?, ?)",
        (chat_id, session_token, employee_id, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def delete_session(chat_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM telegram_sessions WHERE chat_id = ?", (chat_id,))
    conn.execute("DELETE FROM conversation_history WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def get_history(chat_id: int) -> list:
    import json
    conn = get_conn()
    row = conn.execute(
        "SELECT history FROM conversation_history WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    conn.close()
    return json.loads(row["history"]) if row else []


def save_history(chat_id: int, history: list) -> None:
    import json
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO conversation_history VALUES (?, ?)",
        (chat_id, json.dumps(history)),
    )
    conn.commit()
    conn.close()
