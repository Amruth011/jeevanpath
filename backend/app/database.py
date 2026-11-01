import os
import sqlite3
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


LOCAL_DATABASE_PATH = Path(__file__).parents[2] / "data" / "jeevanpath.db"
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_PATH = Path(
    os.getenv(
        "JEEVANPATH_DATABASE_PATH",
        "/tmp/jeevanpath.db" if os.getenv("VERCEL") == "1" else str(LOCAL_DATABASE_PATH),
    )
)


POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversation_messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    transcript TEXT NOT NULL,
    response_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS escalations (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    synthetic BOOLEAN NOT NULL DEFAULT TRUE,
    test_record BOOLEAN NOT NULL DEFAULT TRUE
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
    synthetic BOOLEAN NOT NULL DEFAULT TRUE,
    test_record BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(id),
    text TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    tone TEXT NOT NULL,
    synthetic BOOLEAN NOT NULL DEFAULT TRUE
);
"""


class PostgresConnection:
    def __init__(self, url: str):
        self._db = psycopg.connect(url, row_factory=dict_row)

    def __enter__(self):
        self._db.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._db.__exit__(exc_type, exc_value, traceback)

    @staticmethod
    def _sql(query: str) -> str:
        return query.replace("INSERT OR IGNORE", "INSERT").replace("VALUES (", "VALUES (")

    def execute(self, query: str, params=()):
        query = self._sql(query).replace("?", "%s")
        if query.lstrip().upper().startswith("INSERT INTO") and "ON CONFLICT" not in query.upper():
            query = f"{query.rstrip(';')} ON CONFLICT DO NOTHING"
        return self._db.execute(query, params)

    def executemany(self, query: str, params):
        query = self._sql(query).replace("?", "%s")
        if query.lstrip().upper().startswith("INSERT INTO") and "ON CONFLICT" not in query.upper():
            query = f"{query.rstrip(';')} ON CONFLICT DO NOTHING"
        return self._db.executemany(query, params)

    def close(self):
        self._db.close()


def _postgres_connection() -> PostgresConnection:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is required in Vercel production. Configure Neon PostgreSQL before serving requests."
        )
    db = PostgresConnection(DATABASE_URL)
    db._db.execute(POSTGRES_SCHEMA)
    return db


def connection() -> sqlite3.Connection | PostgresConnection:
    if DATABASE_URL:
        return _postgres_connection()
    if os.getenv("VERCEL") == "1":
        raise RuntimeError(
            "DATABASE_URL is required in Vercel production. SQLite is local-development only."
        )
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
