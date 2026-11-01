from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


RiskLevel = Literal["none", "low", "medium", "high", "unknown"]


@dataclass
class Patient:
    id: str
    name: str
    synthetic: bool = True


@dataclass
class Conversation:
    id: str
    patient_id: str
    messages: list[dict] = field(default_factory=list)


@dataclass
class Escalation:
    id: str
    conversation_id: str
    reason: str
    risk_level: RiskLevel
    status: Literal["open", "resolved"] = "open"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


PATIENTS = [Patient("test-patient-001", "Test Patient")]
CONVERSATIONS = {
    "conversation-001": Conversation("conversation-001", "test-patient-001")
}
ESCALATIONS: list[Escalation] = []


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"
