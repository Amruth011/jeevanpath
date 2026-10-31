"use client";

import { useRef, useState } from "react";

type TurnResponse = {
  transcript: string | null;
  response_text: string | null;
  audio_url: string | null;
  risk_level: string;
  escalation_status: string;
  error?: string | null;
};

export default function VoiceTestPage() {
  const [recording, setRecording] = useState(false);
  const [result, setResult] = useState<TurnResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  async function toggleRecording() {
    setError(null);
    if (recording) {
      recorder.current?.stop();
      setRecording(false);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      chunks.current = [];
      mediaRecorder.ondataavailable = (event) => chunks.current.push(event.data);
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const form = new FormData();
        form.append("audio", new Blob(chunks.current, { type: "audio/webm" }), "patient.webm");
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/conversations/conversation-001/turn`, { method: "POST", body: form });
        const body = await response.json() as TurnResponse;
        if (!response.ok || body.error) setError(body.error ?? "The voice turn could not be completed.");
        setResult(body);
      };
      recorder.current = mediaRecorder;
      mediaRecorder.start();
      setRecording(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Microphone access is unavailable.");
    }
  }

  return <main>
    <h1>JeevanPath voice test</h1>
    <p>Synthetic patient data only. This prototype does not diagnose or change medicines.</p>
    <button onClick={toggleRecording}>{recording ? "Stop and send" : "Start recording"}</button>
    {error && <p role="alert" style={{ color: "darkred" }}>Provider or recording error: {error}</p>}
    {result && <section aria-live="polite">
      <h2>Turn result</h2>
      <p><strong>Transcript:</strong> {result.transcript ?? "Unavailable"}</p>
      <p><strong>Response:</strong> {result.response_text ?? "Unavailable"}</p>
      <p><strong>Risk:</strong> {result.risk_level} | <strong>Escalation:</strong> {result.escalation_status}</p>
      {result.audio_url && <audio controls src={result.audio_url}>Your browser cannot play this audio.</audio>}
    </section>}
  </main>;
}
