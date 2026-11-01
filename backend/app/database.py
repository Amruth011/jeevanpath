import os
import sqlite3
from pathlib import Path


LOCAL_DATABASE_PATH = Path(__file__).parents[2] / "data" / "jeevanpath.db"
DATABASE_PATH = Path(
    os.getenv(
        "JEEVANPATH_DATABASE_PATH",
        "/tmp/jeevanpath.db" if os.getenv("VERCEL") == "1" else str(LOCAL_DATABASE_PATH),
    )
)


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
            created_at TEXT NOT NULL,
            synthetic INTEGER NOT NULL DEFAULT 1,
            test_record INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            case_id TEXT NOT NULL UNIQUE,
            conversation_id TEXT NOT NULL DEFAULT 'conversation-001',
            language TEXT NOT NULL,
            status TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            age INTEGER NOT NULL,
            caregiver TEXT NOT NULL,
            phone TEXT NOT NULL,
            consent TEXT NOT NULL,
            follow_up TEXT NOT NULL,
            synthetic INTEGER NOT NULL DEFAULT 1,
            test_record INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            text TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            tone TEXT NOT NULL,
            synthetic INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        """
    )
    escalation_columns = {row["name"] for row in db.execute("PRAGMA table_info(escalations)")}
    if "synthetic" not in escalation_columns:
        db.execute("ALTER TABLE escalations ADD COLUMN synthetic INTEGER NOT NULL DEFAULT 1")
    if "test_record" not in escalation_columns:
        db.execute("ALTER TABLE escalations ADD COLUMN test_record INTEGER NOT NULL DEFAULT 1")
    patient_columns = {row["name"] for row in db.execute("PRAGMA table_info(patients)")}
    if "conversation_id" not in patient_columns:
        db.execute(
            "ALTER TABLE patients ADD COLUMN conversation_id TEXT NOT NULL DEFAULT 'conversation-001'"
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
            """
            INSERT INTO escalations
            (id, conversation_id, reason, risk_level, status, created_at, synthetic, test_record)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1)
            """,
            (escalation.id, escalation.conversation_id, escalation.reason, escalation.risk_level, escalation.status, escalation.created_at),
        )
