import base64

from fastapi import FastAPI, File, HTTPException, UploadFile

from .config import settings
from .database import connection, save_escalation, save_message
from .models import CONVERSATIONS, ESCALATIONS, PATIENTS, Escalation, new_id
from .providers import (
    GnaniPrisma,
    GnaniTimbre,
    ProviderConfigurationError,
    ProviderError,
)
from .safety import evaluate_transcript, validate_response
from .schemas import ModelEvent, PatientResponse, TestCaseResponse, TurnResponse
from .seed import seed_demo_data_if_missing

app = FastAPI(title="JeevanPath API", version="0.1.0")


@app.middleware("http")
async def initialize_database(request, call_next):
    with connection():
        pass
    if settings.demo_seed:
        seed_demo_data_if_missing()
    return await call_next(request)


def _providers():
    return (
        GnaniPrisma("Prisma", settings.prisma_url, settings.prisma_api_key, settings.stt_language_code),
        GnaniTimbre("Timbre", settings.timbre_url, settings.timbre_api_key, settings.tts_voice),
    )


def _patient_from_row(row) -> dict:
    patient = dict(row)
    patient["synthetic"] = bool(patient["synthetic"])
    patient["test_record"] = bool(patient["test_record"])
    return patient


def _patient_detail(patient_id: str) -> dict | None:
    with connection() as db:
        patient = db.execute(
            "SELECT * FROM patients WHERE id = ? AND synthetic = 1 AND test_record = 1",
            (patient_id,),
        ).fetchone()
        if patient is None:
            return None
        result = _patient_from_row(patient)
        result["activities"] = [
            dict(row)
            for row in db.execute(
                """
                SELECT id, text, occurred_at, tone, synthetic
                FROM activities
                WHERE patient_id = ? AND synthetic = 1
                ORDER BY occurred_at DESC
                """,
                (patient_id,),
            )
        ]
        result["escalations"] = []
        return result


@app.get("/health")
@app.get("/api/health")
async def health():
    prisma, timbre = _providers()
    return {
        "status": "ok",
        "synthetic_data": True,
        "providers": {
            "prisma": prisma.health(),
            "timbre": timbre.health(),
            "evon": {"configured": False, "status": "not_implemented"},
        },
    }


@app.get("/api/patients")
async def patients():
    with connection() as db:
        rows = db.execute(
            "SELECT * FROM patients WHERE synthetic = 1 AND test_record = 1 ORDER BY name"
        ).fetchall()
    return [_patient_from_row(row) for row in rows]


@app.get("/api/test-case", response_model=TestCaseResponse)
async def test_case():
    with connection() as db:
        patient = db.execute(
            """
            SELECT id, name, conversation_id
            FROM patients
            WHERE id = 'test-patient-001'
              AND conversation_id = 'conversation-001'
              AND synthetic = 1
              AND test_record = 1
            """
        ).fetchone()
    if patient is None:
        return TestCaseResponse(
            available=False,
            requirement="No synthetic test case exists. Set DEMO_SEED=true and redeploy the demo.",
            synthetic=True,
            test_record=True,
        )
    return TestCaseResponse(
        available=True,
        patient_id=patient["id"],
        conversation_id=patient["conversation_id"],
        patient_name=patient["name"],
        synthetic=True,
        test_record=True,
    )


@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
async def patient_detail(patient_id: str):
    patient = _patient_detail(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


@app.get("/api/activity")
async def activity():
    with connection() as db:
        rows = db.execute(
            """
            SELECT a.id, a.patient_id, p.name AS patient_name, a.text,
                   a.occurred_at, a.tone, a.synthetic
            FROM activities a
            JOIN patients p ON p.id = a.patient_id
            WHERE a.synthetic = 1 AND p.synthetic = 1 AND p.test_record = 1
            ORDER BY a.occurred_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/escalations")
async def escalations():
    with connection() as db:
        rows = db.execute(
            """
            SELECT e.id, e.conversation_id, e.reason, e.risk_level,
                   e.status, e.created_at, e.synthetic, e.test_record
            FROM escalations e
            WHERE e.synthetic = 1 AND e.test_record = 1
            ORDER BY e.created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/overview")
async def overview():
    with connection() as db:
        counts = db.execute(
            """
            SELECT COUNT(*) AS patient_count,
                   SUM(CASE WHEN risk_level = 'low' THEN 1 ELSE 0 END) AS low_risk,
                   SUM(CASE WHEN risk_level = 'medium' THEN 1 ELSE 0 END) AS medium_risk,
                   SUM(CASE WHEN risk_level = 'high' THEN 1 ELSE 0 END) AS high_risk
            FROM patients
            WHERE synthetic = 1 AND test_record = 1
            """
        ).fetchone()
        pending = db.execute(
            "SELECT COUNT(*) FROM escalations WHERE status = 'open' AND synthetic = 1 AND test_record = 1"
        ).fetchone()[0]
        follow_ups = db.execute(
            "SELECT COUNT(*) FROM patients WHERE synthetic = 1 AND test_record = 1 AND follow_up != ''"
        ).fetchone()[0]
    return {
        "patient_count": counts["patient_count"],
        "pending_escalations": pending,
        "follow_ups": follow_ups,
        "unanswered_calls": 0,
        "risk_counts": {
            "low": counts["low_risk"] or 0,
            "medium": counts["medium_risk"] or 0,
            "high": counts["high_risk"] or 0,
        },
        "synthetic": True,
        "test_record": True,
    }


@app.post("/api/conversations/{conversation_id}/turn", response_model=TurnResponse)
async def conversation_turn(conversation_id: str, audio: UploadFile = File(...)):
    if conversation_id not in CONVERSATIONS:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    events = [ModelEvent(model="prisma", status="started", detail="Transcribing audio.")]
    prisma, timbre = _providers()
    try:
        transcript = await prisma.transcribe(
            await audio.read(), audio.content_type or "audio/webm", audio.filename or "audio.webm"
        )
        events[0] = ModelEvent(model="prisma", status="completed", detail="Transcript received.")
    except (ProviderConfigurationError, ProviderError) as exc:
        events[0] = ModelEvent(model="prisma", status="failed", detail=str(exc))
        return TurnResponse(
            transcript=None, response_text=None, audio_url=None, risk_level="unknown",
            escalation_status="error", model_events=events, error=str(exc),
        )

    safety = evaluate_transcript(transcript)
    events.append(ModelEvent(
        model="safety", status="completed",
        detail=safety.reason or "No deterministic safety escalation required.",
    ))
    if safety.escalate:
        ESCALATIONS.append(Escalation(new_id("escalation"), conversation_id, safety.reason or "Safety review required.", safety.risk_level))
        save_escalation(ESCALATIONS[-1])
        response = "I cannot safely answer this without a healthcare professional. Please contact your care team now. If this feels urgent or life-threatening, call your local emergency service."
        CONVERSATIONS[conversation_id].messages.append({"transcript": transcript, "response": response})
        save_message(conversation_id, transcript, response)
        events.extend([
            ModelEvent(model="evon", status="skipped", detail="No Evon API is implemented; safety rules require human review."),
            ModelEvent(model="timbre", status="skipped", detail="Safety escalation was not sent to TTS."),
        ])
        return TurnResponse(transcript=transcript, response_text=response, audio_url=None, risk_level=safety.risk_level, escalation_status="open", model_events=events)

    events.append(ModelEvent(model="evon", status="skipped", detail="No Evon reasoning API is implemented."))
    response = "I do not have enough verified discharge information to answer safely. Please contact your care team for help."
    events.append(ModelEvent(model="timbre", status="started", detail="Synthesizing safe uncertainty response."))
    try:
        if not validate_response(response):
            raise ProviderError("Safety response validation failed.")
        audio_bytes = await timbre.synthesize(response)
        events[-1] = ModelEvent(model="timbre", status="completed", detail="Audio received.")
    except (ProviderConfigurationError, ProviderError) as exc:
        events[-1] = ModelEvent(model="timbre", status="failed", detail=str(exc))
        return TurnResponse(transcript=transcript, response_text=None, audio_url=None, risk_level="unknown", escalation_status="error", model_events=events, error=str(exc))

    CONVERSATIONS[conversation_id].messages.append({"transcript": transcript, "response": response})
    save_message(conversation_id, transcript, response)
    audio_url = f"data:audio/wav;base64,{base64.b64encode(audio_bytes).decode('ascii')}"
    return TurnResponse(transcript=transcript, response_text=response, audio_url=audio_url, risk_level="unknown", escalation_status="open", model_events=events)
