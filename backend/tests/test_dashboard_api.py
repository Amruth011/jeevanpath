from dataclasses import replace

from fastapi.testclient import TestClient

from app.database import connection
from app.main import app
from app.config import settings
from app.seed import seed_demo_data_if_missing, seed_test_data


def test_fresh_database_creates_tables_and_returns_empty_results(monkeypatch, tmp_path):
    monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "fresh.db")
    client = TestClient(app)

    assert client.get("/api/overview").json()["patient_count"] == 0
    assert client.get("/api/patients").json() == []
    assert client.get("/api/activity").json() == []
    assert client.get("/api/escalations").json() == []


def test_seed_creates_one_test_patient_and_api_data(monkeypatch, tmp_path):
    monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "test.db")
    seed_test_data()
    seed_test_data()
    client = TestClient(app)

    patients = client.get("/api/patients")
    overview = client.get("/api/overview")
    detail = client.get("/api/patients/test-patient-001")

    assert patients.status_code == 200
    assert len(patients.json()) == 2
    assert patients.json()[0]["test_record"] is True
    assert overview.json()["patient_count"] == 2
    assert overview.json()["synthetic"] is True
    assert detail.status_code == 200
    assert detail.json()["activities"]


def test_demo_seed_only_runs_when_enabled(monkeypatch, tmp_path):
    monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "demo.db")
    client = TestClient(app)

    monkeypatch.setattr("app.main.settings", replace(settings, demo_seed=False))
    assert client.get("/api/patients").json() == []

    monkeypatch.setattr("app.main.settings", replace(settings, demo_seed=True))
    assert len(client.get("/api/patients").json()) == 2
    seed_demo_data_if_missing()
    assert len(client.get("/api/patients").json()) == 2


def test_demo_seed_does_not_run_when_unset(monkeypatch, tmp_path):
    monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "unset.db")
    monkeypatch.setattr("app.main.settings", replace(settings, demo_seed=False))

    response = TestClient(app).get("/api/patients")

    assert response.status_code == 200
    assert response.json() == []


def test_dashboard_api_returns_empty_data_without_seed(monkeypatch, tmp_path):
    monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "empty.db")
    connection().close()
    client = TestClient(app)

    assert client.get("/api/patients").json() == []
    assert client.get("/api/activity").json() == []
    assert client.get("/api/escalations").json() == []
    assert client.get("/api/overview").json()["patient_count"] == 0
    assert client.get("/api/overview").json()["risk_counts"] == {"low": 0, "medium": 0, "high": 0}
    assert client.get("/api/patients/missing").status_code == 404
