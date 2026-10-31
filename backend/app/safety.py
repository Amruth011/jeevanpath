import re
from dataclasses import dataclass

from .models import RiskLevel


@dataclass(frozen=True)
class SafetyResult:
    risk_level: RiskLevel
    escalate: bool
    reason: str | None = None


_DANGER = re.compile(
    r"\b(chest pain|can't breathe|cannot breathe|difficulty breathing|"
    r"severe bleeding|passed out|unconscious|stroke|face drooping|"
    r"suicid(?:e|al)|seizure)\b",
    re.IGNORECASE,
)
_MEDICATION = re.compile(
    r"\b(increase|decrease|change|double|skip|stop|extra)\b.{0,30}\b"
    r"(dose|medicine|medication|tablet|pill)\b",
    re.IGNORECASE,
)
_UNCERTAIN = re.compile(r"\b(not sure|don't know|unclear|forgot|can't remember)\b", re.IGNORECASE)


def evaluate_transcript(transcript: str | None) -> SafetyResult:
    if not transcript or not transcript.strip():
        return SafetyResult("unknown", True, "The voice transcript was empty or unavailable.")
    if _DANGER.search(transcript):
        return SafetyResult("high", True, "The patient reported a possible danger symptom.")
    if _MEDICATION.search(transcript):
        return SafetyResult("high", True, "Medication changes require a qualified human clinician.")
    if _UNCERTAIN.search(transcript):
        return SafetyResult("unknown", True, "The patient or discharge instruction is uncertain.")
    return SafetyResult("none", False)


def validate_response(text: str) -> bool:
    lowered = text.lower()
    prohibited = ("you have ", "diagnosis", "take more", "increase your dose", "decrease your dose")
    return not any(phrase in lowered for phrase in prohibited)
