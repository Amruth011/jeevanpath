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
async def test_prisma_rejects_empty_audio_before_request():
    with pytest.raises(Exception, match="recording was empty"):
        await GnaniPrisma("Prisma", "https://example.test", "secret").transcribe(b"", "audio/webm")


@pytest.mark.asyncio
async def test_prisma_includes_safe_provider_error_detail(monkeypatch):
    response = httpx.Response(
        400,
        text='{"type":"EMPTY_AUDIO","message":"Empty audio file received"}',
        request=httpx.Request("POST", "https://example.test"),
    )
    client = FakeAsyncClient(response)
    monkeypatch.setattr("app.providers.httpx.AsyncClient", lambda **kwargs: client)

    with pytest.raises(Exception, match="EMPTY_AUDIO"):
        await GnaniPrisma("Prisma", "https://example.test", "secret").transcribe(
            b"audio", "audio/webm"
        )


@pytest.mark.asyncio
async def test_timbre_uses_documented_json_and_returns_audio(monkeypatch):
    response = httpx.Response(200, content=b"RIFFfake-wav", request=httpx.Request("POST", "https://example.test"))
    client = FakeAsyncClient(response)
    monkeypatch.setattr("app.providers.httpx.AsyncClient", lambda **kwargs: client)
    provider = GnaniTimbre(
        "Timbre", "https://api.vachana.ai/api/v1/tts/inference", "secret",
        "timbre-v2.5", "Pranav", "en-IN",
    )

    assert await provider.synthesize("hello") == b"RIFFfake-wav"
    assert client.url == "https://api.vachana.ai/api/v1/tts/inference"
    assert client.kwargs["headers"]["X-API-Key-ID"] == "secret"
    assert client.kwargs["headers"]["X-API-Request-ID"]
    assert client.kwargs["json"]["model"] == "timbre-v2.5"
    assert client.kwargs["json"]["voice"] == "Pranav"
    assert client.kwargs["json"]["language"] == "en-IN"
    assert client.kwargs["json"]["speed"] == 1.0
    assert client.kwargs["json"]["audio_config"] == {
        "sample_rate": 48000,
        "num_channels": 1,
        "sample_width": 2,
        "encoding": "linear_pcm",
        "container": "wav",
    }


@pytest.mark.asyncio
async def test_timbre_surfaces_safe_error_body(monkeypatch):
    response = httpx.Response(
        400,
        text='{"error":{"type":"INVALID_MODEL","message":"Model is not supported"}}',
        request=httpx.Request("POST", "https://example.test"),
    )
    client = FakeAsyncClient(response)
    monkeypatch.setattr("app.providers.httpx.AsyncClient", lambda **kwargs: client)

    with pytest.raises(Exception, match="INVALID_MODEL"):
        await GnaniTimbre(
            "Timbre", "https://example.test", "secret",
            "timbre-v2.5", "Pranav", "en-IN",
        ).synthesize("hello")


@pytest.mark.asyncio
async def test_timbre_rejects_undocumented_configuration():
    with pytest.raises(Exception, match="not documented"):
        await GnaniTimbre(
            "Timbre", "https://example.test", "secret",
            "timbre-v2.0", "Pranav", "en-IN",
        ).synthesize("hello")


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
