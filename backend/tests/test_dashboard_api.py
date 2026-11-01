from fastapi.testclient import TestClient

from app.database import connection
from app.main import app
from app.seed import seed_test_data


def test_seed_creates_one_test_patient_and_api_data(monkeypatch, tmp_path):
    monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "test.db")
    seed_test_data()
    seed_test_data()
    client = TestClient(app)

    patients = client.get("/api/patients")
    overview = client.get("/api/overview")
    detail = client.get("/api/patients/test-patient-001")

    assert patients.status_code == 200
    assert len(patients.json()) == 1
    assert patients.json()[0]["test_record"] is True
    assert overview.json()["patient_count"] == 1
    assert overview.json()["synthetic"] is True
    assert detail.status_code == 200
    assert detail.json()["activities"]


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
