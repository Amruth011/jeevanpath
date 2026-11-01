from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

import httpx


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderError(RuntimeError):
    pass


TTS_MODEL_VOICES = {
    "timbre-v2.5": {
        "Ambuja", "Asmita", "Bhavna", "Brinda", "Chitra", "Deepak", "Devika", "Dhruva",
        "Falak", "Girish", "Hemraj", "Ishaan", "Jalaj", "Jwala", "Kaveri", "Kavin",
        "Kirra", "Lavanya", "Lehara", "Mehuli", "Nalini", "Noopur", "Omkar", "Poorvi",
        "Pranav", "Reshma", "Riyaan", "Roopesh", "Saanvi", "Shlok", "Suhana", "Trisha",
        "Trupti", "Urmila", "Varuni", "Vedika", "Veera", "Vikrant", "Yashvi", "Yukti",
        "Zahira", "Zayan",
    },
    "timbre-v3.0": {
        "Avinash", "Chetana", "Devansh", "Kalpana", "Lakshmi", "Prakash", "Shivani",
        "Shubham", "Tarika", "Vasudha", "Yashraj", "Harshad", "Riyaa",
    },
}
TTS_LANGUAGES = {
    "auto", "hi-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN",
    "mr-IN", "pa-IN", "bn-IN", "gu-IN", "hi-en",
}


def _endpoint(url: str, path: str) -> str:
    return url if url.rstrip("/").endswith(path) else f"{url.rstrip('/')}{path}"


class SttProvider(Protocol):
    async def transcribe(self, audio: bytes, content_type: str, filename: str) -> str: ...


class TtsProvider(Protocol):
    async def synthesize(self, text: str) -> bytes: ...


@dataclass
class GnaniProvider:
    name: str
    url: str | None
    api_key: str | None

    def _check_config(self) -> None:
        if not self.url or not self.api_key:
            raise ProviderConfigurationError(
                f"Gnani {self.name} configuration is missing. Set the corresponding URL and API key."
            )

    def health(self) -> dict[str, str | bool]:
        if not self.url or not self.api_key:
            return {"configured": False, "status": "missing_configuration"}
        return {"configured": True, "status": "configured", "url": self.url}


@dataclass
class GnaniPrisma(GnaniProvider):
    language_code: str = "en-IN"

    async def transcribe(self, audio: bytes, content_type: str, filename: str = "audio.webm") -> str:
        self._check_config()
        if not audio:
            raise ProviderError("Gnani Prisma request was not sent: the recording was empty.")
        headers = {"X-API-Key-ID": self.api_key, "X-API-Request-ID": str(uuid4())}
        data = {"language_code": self.language_code, "model": "prisma-v3.0", "format": "transcribe"}
        files = {"audio_file": (filename, audio, content_type)}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(_endpoint(self.url, "/stt/v3"), headers=headers, data=data, files=files)
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            suffix = f" ({detail})" if detail else ""
            raise ProviderError(
                f"Gnani Prisma request failed with HTTP {exc.response.status_code}{suffix}"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"Gnani Prisma request failed: {exc}") from exc
        transcript = result.get("transcript")
        if not isinstance(transcript, str):
            raise ProviderError("Gnani Prisma response did not contain transcript.")
        return transcript


@dataclass
class GnaniTimbre(GnaniProvider):
    model: str = "timbre-v2.5"
    voice: str = "Pranav"
    language_code: str = "en-IN"

    def _check_tts_config(self) -> None:
        if self.model not in TTS_MODEL_VOICES:
            raise ProviderConfigurationError(
                f"Gnani Timbre model {self.model!r} is not documented. "
                "Use timbre-v2.5 or timbre-v3.0."
            )
        if self.voice not in TTS_MODEL_VOICES[self.model]:
            raise ProviderConfigurationError(
                f"Gnani Timbre voice {self.voice!r} is not documented for model {self.model!r}."
            )
        if self.language_code not in TTS_LANGUAGES:
            raise ProviderConfigurationError(
                f"Gnani Timbre language {self.language_code!r} is not documented."
            )

    async def synthesize(self, text: str) -> bytes:
        self._check_config()
        self._check_tts_config()
        headers = {
            "X-API-Key-ID": self.api_key,
            "X-API-Request-ID": str(uuid4()),
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "voice": self.voice,
            "model": self.model,
            "language": self.language_code,
            "speed": 1.0,
            "audio_config": {"sample_rate": 48000, "encoding": "linear_pcm", "container": "wav"},
        }
        payload["audio_config"].update({"num_channels": 1, "sample_width": 2})
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    _endpoint(self.url, "/api/v1/tts/inference"), headers=headers, json=payload
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            suffix = f" ({detail})" if detail else ""
            raise ProviderError(
                f"Gnani Timbre request failed with HTTP {exc.response.status_code}{suffix}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Gnani Timbre request failed: {exc}") from exc
        if not response.content:
            raise ProviderError("Gnani Timbre response contained no audio.")
        return response.content
