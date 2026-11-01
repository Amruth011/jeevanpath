import pytest

from app import database


def test_vercel_requires_database_url(monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", None)
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        database.connection()


def test_local_database_remains_sqlite(monkeypatch, tmp_path):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setattr(database, "DATABASE_URL", None)
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "local.db")
    with database.connection() as db:
        assert db.execute("SELECT 1 AS value").fetchone()["value"] == 1
