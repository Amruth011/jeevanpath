import base64

from fastapi import FastAPI, File, HTTPException, UploadFile

from .config import settings
from .database import save_escalation, save_message
from .models import CONVERSATIONS, ESCALATIONS, PATIENTS, Escalation, new_id
from .providers import (
    GnaniPrisma,
    GnaniTimbre,
    ProviderConfigurationError,
    ProviderError,
)
from .safety import evaluate_transcript, validate_response
from .schemas import ModelEvent, TurnResponse

app = FastAPI(title="JeevanPath API", version="0.1.0")


def _providers():
    return (
        GnaniPrisma("Prisma", settings.prisma_url, settings.prisma_api_key, settings.stt_language_code),
        GnaniTimbre("Timbre", settings.timbre_url, settings.timbre_api_key, settings.tts_voice),
    )


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
    return [patient.__dict__ for patient in PATIENTS]


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
