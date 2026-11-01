import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.whatsapp import WhatsAppCloud


class FakeAsyncClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return next(self.responses)

    async def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return next(self.responses)


@pytest.mark.asyncio
async def test_whatsapp_downloads_media_with_bearer_token(monkeypatch):
    client = FakeAsyncClient(
        [
            httpx.Response(200, json={"url": "https://cdn.example/audio.ogg"}, request=httpx.Request("GET", "https://example.test")),
            httpx.Response(200, content=b"audio", headers={"content-type": "audio/ogg"}, request=httpx.Request("GET", "https://cdn.example/audio.ogg")),
        ]
    )
    monkeypatch.setattr("app.whatsapp.httpx.AsyncClient", lambda **kwargs: client)

    audio, content_type = await WhatsAppCloud("token", "phone").download_media("media-1")

    assert audio == b"audio"
    assert content_type == "audio/ogg"
    assert client.calls[0][2]["headers"]["Authorization"] == "Bearer token"
    assert client.calls[1][1] == "https://cdn.example/audio.ogg"


def test_whatsapp_webhook_verification(monkeypatch):
    from dataclasses import replace

    monkeypatch.setattr("app.main.settings", replace(settings, whatsapp_verify_token="verify"))
    response = TestClient(app).get(
        "/api/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.json() == 12345


def test_whatsapp_health_does_not_expose_token(monkeypatch):
    from dataclasses import replace

    monkeypatch.setattr(
        "app.main.settings",
        replace(settings, whatsapp_verify_token="verify", whatsapp_access_token="secret", whatsapp_phone_number_id="phone"),
    )
    body = TestClient(app).get("/api/health").json()
    assert body["providers"]["whatsapp"]["configured"] is True
    assert "secret" not in str(body)
