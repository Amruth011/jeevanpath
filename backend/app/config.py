from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).parents[1] / ".env")


@dataclass(frozen=True)
class Settings:
    prisma_url: str | None = os.getenv("GNANI_PRISMA_URL")
    prisma_api_key: str | None = os.getenv("GNANI_PRISMA_API_KEY")
    timbre_url: str | None = os.getenv("GNANI_TIMBRE_URL")
    timbre_api_key: str | None = os.getenv("GNANI_TIMBRE_API_KEY")
    stt_language_code: str = os.getenv("GNANI_STT_LANGUAGE_CODE", "en-IN")
    tts_voice: str = os.getenv("GNANI_TTS_VOICE", "Pranav")


settings = Settings()
