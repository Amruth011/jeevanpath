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


class PatientResponse(BaseModel):
    id: str
    name: str
    case_id: str
    conversation_id: str
    language: str
    status: str
    risk_level: RiskLevel
    age: int
    caregiver: str
    phone: str
    consent: str
    follow_up: str
    synthetic: bool
    test_record: bool
    activities: list[dict]
    escalations: list[dict]


class TestCaseResponse(BaseModel):
    available: bool
    requirement: str | None = None
    patient_id: str | None = None
    conversation_id: str | None = None
    patient_name: str | None = None
    synthetic: bool
    test_record: bool
