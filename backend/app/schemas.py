from typing import Literal
from pydantic import BaseModel

from .models import RiskLevel


class ModelEvent(BaseModel):
    model: Literal["prisma", "evon", "timbre", "safety"]
    status: Literal["started", "completed", "skipped", "failed"]
    detail: str


class TurnResponse(BaseModel):
    transcript: str | None
    response_text: str | None
    audio_url: str | None
    risk_level: RiskLevel
    escalation_status: Literal["not_required", "open", "error"]
    model_events: list[ModelEvent]
    error: str | None = None
