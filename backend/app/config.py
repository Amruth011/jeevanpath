from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).parents[1] / ".env")


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() == "true"


@dataclass(frozen=True)
class Settings:
    prisma_url: str | None = os.getenv("GNANI_PRISMA_URL")
    prisma_api_key: str | None = os.getenv("GNANI_PRISMA_API_KEY")
    timbre_url: str | None = os.getenv("GNANI_TIMBRE_URL")
    timbre_api_key: str | None = os.getenv("GNANI_TIMBRE_API_KEY")
    stt_language_code: str = os.getenv("GNANI_STT_LANGUAGE_CODE", "en-IN")
    tts_model: str = os.getenv("GNANI_TTS_MODEL", "timbre-v2.5")
    tts_voice: str = os.getenv("GNANI_TTS_VOICE", "Pranav")
    tts_language_code: str = os.getenv("GNANI_TTS_LANGUAGE_CODE", "en-IN")
    demo_seed: bool = _env_flag("DEMO_SEED")


settings = Settings()
