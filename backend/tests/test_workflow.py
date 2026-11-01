from fastapi.testclient import TestClient

from app.main import app
from app.providers import GnaniPrisma, GnaniTimbre


class FakePrisma(GnaniPrisma):
    async def transcribe(self, audio, content_type, filename):
        return "I have chest pain"


class FakeTimbre(GnaniTimbre):
    async def synthesize(self, text):
        return b"RIFFfake-wav"


def test_api_health_matches_health():
    client = TestClient(app)
    assert client.get("/api/health").json() == client.get("/health").json()


def test_dangerous_turn_skips_reasoning_and_tts(monkeypatch):
    monkeypatch.setattr("app.main._providers", lambda: (FakePrisma("p", "u", "k"), FakeTimbre("t", "u", "k")))
    response = TestClient(app).post(
        "/api/conversations/conversation-001/turn",
        files={"audio": ("patient.webm", b"audio", "audio/webm")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "high"
    assert body["escalation_status"] == "open"
    assert body["audio_url"] is None
    assert [event["status"] for event in body["model_events"]][-2:] == ["skipped", "skipped"]


def test_missing_credentials_is_clear(monkeypatch):
    monkeypatch.setattr(
        "app.main._providers",
        lambda: (GnaniPrisma("Prisma", None, None), GnaniTimbre("Timbre", None, None)),
    )
    response = TestClient(app).post(
        "/api/conversations/conversation-001/turn",
        files={"audio": ("patient.webm", b"audio", "audio/webm")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["escalation_status"] == "error"
    assert "configuration is missing" in body["error"]
