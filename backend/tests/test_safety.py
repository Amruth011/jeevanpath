from app.safety import evaluate_transcript


def test_danger_symptom_escalates():
    result = evaluate_transcript("I have chest pain")
    assert result.escalate is True
    assert result.risk_level == "high"


def test_medication_change_escalates():
    assert evaluate_transcript("Can I increase my dose?").escalate is True


def test_normal_question_is_allowed():
    result = evaluate_transcript("When is my follow-up appointment?")
    assert result.escalate is False
    assert result.risk_level == "none"


def test_missing_transcript_escalates_as_unknown():
    result = evaluate_transcript(None)
    assert result.risk_level == "unknown"
    assert result.escalate is True
