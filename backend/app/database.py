import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).parents[2] / "data" / "jeevanpath.db"


def connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            transcript TEXT NOT NULL,
            response_text TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS escalations (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    return db


def save_message(conversation_id: str, transcript: str, response_text: str | None) -> None:
    with connection() as db:
        db.execute(
            "INSERT INTO conversation_messages (conversation_id, transcript, response_text) VALUES (?, ?, ?)",
            (conversation_id, transcript, response_text),
        )


def save_escalation(escalation) -> None:
    with connection() as db:
        db.execute(
            "INSERT INTO escalations (id, conversation_id, reason, risk_level, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (escalation.id, escalation.conversation_id, escalation.reason, escalation.risk_level, escalation.status, escalation.created_at),
        )
