import httpx
import pytest

from app.providers import GnaniPrisma, GnaniTimbre


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, **kwargs):
        self.url = url
        self.kwargs = kwargs
        return self.response


@pytest.mark.asyncio
async def test_prisma_uses_documented_multipart_contract(monkeypatch):
    response = httpx.Response(200, json={"transcript": "hello"}, request=httpx.Request("POST", "https://example.test"))
    client = FakeAsyncClient(response)
    monkeypatch.setattr("app.providers.httpx.AsyncClient", lambda **kwargs: client)
    provider = GnaniPrisma("Prisma", "https://api.vachana.ai/stt/v3", "secret", "en-IN")

    assert await provider.transcribe(b"audio", "audio/webm", "patient.webm") == "hello"
    assert client.url == "https://api.vachana.ai/stt/v3"
    assert client.kwargs["headers"]["X-API-Key-ID"] == "secret"
    assert "Authorization" not in client.kwargs["headers"]
    assert client.kwargs["data"]["model"] == "prisma-v3.0"
    assert client.kwargs["files"]["audio_file"][0] == "patient.webm"


@pytest.mark.asyncio
async def test_timbre_uses_documented_json_and_returns_audio(monkeypatch):
    response = httpx.Response(200, content=b"RIFFfake-wav", request=httpx.Request("POST", "https://example.test"))
    client = FakeAsyncClient(response)
    monkeypatch.setattr("app.providers.httpx.AsyncClient", lambda **kwargs: client)
    provider = GnaniTimbre("Timbre", "https://api.vachana.ai/api/v1/tts/inference", "secret", "Pranav")

    assert await provider.synthesize("hello") == b"RIFFfake-wav"
    assert client.url == "https://api.vachana.ai/api/v1/tts/inference"
    assert client.kwargs["headers"]["X-API-Key-ID"] == "secret"
    assert client.kwargs["json"]["model"] == "timbre-v2.0"
    assert client.kwargs["json"]["audio_config"]["container"] == "wav"


def test_health_never_returns_api_key(monkeypatch):
    from app.main import app
    from fastapi.testclient import TestClient

    monkeypatch.setattr(
        "app.main._providers",
        lambda: (
            GnaniPrisma("Prisma", "https://example.test/stt/v3", "secret-value"),
            GnaniTimbre("Timbre", "https://example.test/tts", "secret-value"),
        ),
    )
    body = TestClient(app).get("/health").json()
    assert "secret-value" not in str(body)
    assert body["providers"]["prisma"]["status"] == "configured"
