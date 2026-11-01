export type TurnResponse = {
  transcript: string | null;
  response_text: string | null;
  audio_url: string | null;
  risk_level: string;
  escalation_status: string;
  error?: string | null;
};

const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
const isProduction = process.env.NODE_ENV === "production";

export const API_BASE_URL = isProduction
  ? "/api"
  : configuredApiBaseUrl
    ? `${configuredApiBaseUrl.replace(/\/+$/, "")}/api`
    : "http://localhost:8000/api";
export const MOCK_MODE = !isProduction && !configuredApiBaseUrl;

const mockTurnResponse: TurnResponse = {
  transcript: "I would like to confirm my follow-up appointment.",
  response_text: "Your follow-up is scheduled according to the approved care plan. Please contact your care team if you need help.",
  audio_url: null,
  risk_level: "none",
  escalation_status: "not_required",
};

export async function submitVoiceTurn(audio: Blob): Promise<TurnResponse> {
  if (MOCK_MODE) {
    await new Promise((resolve) => window.setTimeout(resolve, 700));
    return mockTurnResponse;
  }

  const form = new FormData();
  form.append("audio", audio, "patient.webm");
  const response = await fetch(`${API_BASE_URL}/api/conversations/conversation-001/turn`, {
    method: "POST",
    body: form,
  });

  let body: TurnResponse;
  try {
    body = await response.json() as TurnResponse;
  } catch {
    throw new Error("The care service returned an invalid response.");
  }

  if (!response.ok || body.error) {
    throw new Error(body.error ?? "The voice turn could not be completed.");
  }

  return body;
}
