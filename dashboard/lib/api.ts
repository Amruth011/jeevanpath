export type TurnResponse = {
  transcript: string | null;
  response_text: string | null;
  audio_url: string | null;
  risk_level: string;
  escalation_status: string;
  error?: string | null;
};

export type Patient = {
  id: string;
  name: string;
  case_id: string;
  conversation_id: string;
  language: string;
  status: string;
  risk_level: "none" | "low" | "medium" | "high" | "unknown";
  age: number;
  caregiver: string;
  phone: string;
  consent: string;
  follow_up: string;
  synthetic: boolean;
  test_record: boolean;
  activities: Activity[];
  escalations: Escalation[];
};

export type Activity = {
  id: string;
  patient_id: string;
  patient_name?: string;
  text: string;
  occurred_at: string;
  tone: string;
  synthetic: boolean;
};

export type Escalation = {
  id: string;
  conversation_id: string;
  reason: string;
  risk_level: string;
  status: string;
  created_at: string;
  synthetic: boolean;
  test_record: boolean;
};

export type Overview = {
  patient_count: number;
  pending_escalations: number;
  follow_ups: number;
  unanswered_calls: number;
  risk_counts: { low: number; medium: number; high: number };
  synthetic: boolean;
  test_record: boolean;
};

export type TestCase = {
  available: boolean;
  requirement: string | null;
  patient_id: string | null;
  conversation_id: string | null;
  patient_name: string | null;
  synthetic: boolean;
  test_record: boolean;
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

export async function submitVoiceTurn(audio: Blob, conversationId = "conversation-001"): Promise<TurnResponse> {
  if (MOCK_MODE) {
    await new Promise((resolve) => window.setTimeout(resolve, 700));
    return mockTurnResponse;
  }

  const form = new FormData();
  form.append("audio", audio, "patient.webm");
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/turn`, {
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

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`The care service returned ${response.status}.`);
  }
  return response.json() as Promise<T>;
}

export const getOverview = () => getJson<Overview>("/overview");
export const getPatients = () => getJson<Patient[]>("/patients");
export const getPatient = (id: string) => getJson<Patient>(`/patients/${id}`);
export const getActivity = () => getJson<Activity[]>("/activity");
export const getEscalations = () => getJson<Escalation[]>("/escalations");
export const getTestCase = () => getJson<TestCase>("/test-case");
