"use client";

import { useEffect, useMemo, useState } from "react";
import {
  getActivity,
  getEscalations,
  getOverview,
  getPatient,
  getPatients,
  type Activity,
  type Escalation,
  type Overview as OverviewData,
  type Patient,
} from "../lib/api";

type View = "overview" | "patients" | "patient" | "escalations" | "voice";
type Tone = "teal" | "amber" | "red" | "slate" | "green";

function Badge({ children, tone = "slate" }: { children: React.ReactNode; tone?: Tone }) {
  const styles: Record<Tone, string> = {
    teal: "bg-teal/10 text-teal",
    amber: "bg-amber/10 text-amber",
    red: "bg-urgent/10 text-urgent",
    slate: "bg-slate-100 text-slate-600",
    green: "bg-emerald-50 text-emerald-700",
  };
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${styles[tone]}`}>{children}</span>;
}

function TestLabel() {
  return <Badge tone="amber">TEST DATA · Synthetic only</Badge>;
}

function Sidebar({ view, setView, escalationCount }: { view: View; setView: (view: View) => void; escalationCount: number }) {
  return <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">
    <div className="flex h-20 items-center gap-3 border-b border-slate-100 px-7"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal text-lg font-black text-white">J</div><div><p className="text-lg font-black tracking-tight text-navy">JeevanPath</p><p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Care operations</p></div></div>
    <div className="px-4 pt-7"><p className="eyebrow px-3 pb-3">Workspace</p><nav className="space-y-1" aria-label="Primary navigation">
      {([["overview", "Overview", "⌂"], ["patients", "Patients", "◉"], ["escalations", "Escalations", "!"], ["voice", "Voice test", "◌"]] as [View, string, string][]).map(([id, label, icon]) => <button key={id} onClick={() => setView(id)} className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-bold ${view === id ? "bg-mint text-teal" : "text-slate-500 hover:bg-slate-50"}`}><span className="w-5">{icon}</span>{label}{id === "escalations" && escalationCount > 0 && <span className="ml-auto rounded-full bg-urgent px-2 py-0.5 text-[10px] text-white">{escalationCount}</span>}</button>)}
    </nav></div>
    <div className="mt-auto border-t border-slate-100 p-5"><div className="rounded-xl bg-mist p-3"><p className="eyebrow">Development environment</p><p className="mt-1 text-xs leading-5 text-slate-600">TEST DATA only. Do not enter real clinical data without consent.</p></div></div>
  </aside>;
}

function Header({ view, setView }: { view: View; setView: (view: View) => void }) {
  const title = view === "overview" ? "Overview" : view === "patients" ? "Patients" : view === "patient" ? "Patient profile" : view === "escalations" ? "Escalation queue" : "Patient voice test";
  return <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200 bg-white/95 px-5 backdrop-blur md:px-8"><div><p className="hidden text-xs text-slate-400 sm:block">Workspace / {title}</p><h1 className="text-xl font-black text-navy">{title}</h1></div><div className="flex items-center gap-3"><TestLabel /><button onClick={() => setView("voice")} className="button-secondary hidden sm:inline-flex">Voice test</button></div></header>;
}

function StatCard({ label, value, detail, tone = "teal" }: { label: string; value: number; detail: string; tone?: Tone }) {
  const colors: Record<Tone, string> = { teal: "text-teal", amber: "text-amber", red: "text-urgent", slate: "text-slate-600", green: "text-emerald-700" };
  return <div className="panel p-5"><p className="text-sm font-bold text-slate-500">{label}</p><p className={`mt-3 text-3xl font-black tracking-tight ${colors[tone]}`}>{value}</p><p className="mt-3 text-xs font-semibold text-slate-500">{detail}</p></div>;
}

function initials(name: string) {
  return name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}

function Overview({ data, patients, activity, setView }: { data: OverviewData; patients: Patient[]; activity: Activity[]; setView: (view: View) => void }) {
  return <div className="space-y-7"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="eyebrow">Development overview</p><h2 className="mt-1 text-2xl font-black text-navy">Care operations snapshot</h2><p className="mt-1 text-sm text-slate-500">All records shown are synthetic test data.</p></div><TestLabel /></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><StatCard label="Patients" value={data.patient_count} detail="Synthetic test records" /><StatCard label="Pending escalations" value={data.pending_escalations} detail="From the test database" tone="red" /><StatCard label="Follow-ups" value={data.follow_ups} detail="Recorded test follow-ups" tone="amber" /><StatCard label="Unanswered calls" value={data.unanswered_calls} detail="Recorded test calls" tone="slate" /></div>
    <div className="grid gap-5 xl:grid-cols-3"><section className="panel p-5 xl:col-span-2"><p className="eyebrow">Care activity</p><h3 className="mt-1 text-lg font-black text-navy">Recent activity</h3><div className="mt-5 space-y-1">{activity.length ? activity.slice(0, 5).map((item) => <div key={item.id} className="flex items-center gap-3 rounded-xl px-2 py-3"><div className="h-2.5 w-2.5 rounded-full bg-teal" /><div className="min-w-0 flex-1"><p className="text-sm font-bold text-ink">{item.patient_name}</p><p className="truncate text-xs text-slate-500">{item.text}</p></div><span className="text-xs text-slate-400">{new Date(item.occurred_at).toLocaleDateString()}</span></div>) : <EmptyState text="No activity in the test database." />}</div></section>
      <section className="panel p-5"><p className="eyebrow">Safety overview</p><h3 className="mt-1 text-lg font-black text-navy">Risk summary</h3><div className="mt-6 space-y-5">{(["low", "medium", "high"] as const).map((risk) => <div key={risk}><div className="mb-2 flex justify-between text-sm"><span className="font-bold capitalize text-slate-600">{risk} risk</span><span className="font-black text-navy">{data.risk_counts[risk]}</span></div><div className="h-2 rounded-full bg-slate-100"><div className={`h-2 rounded-full ${risk === "high" ? "bg-urgent" : risk === "medium" ? "bg-amber" : "bg-emerald-500"}`} style={{ width: `${data.patient_count ? (data.risk_counts[risk] / data.patient_count) * 100 : 0}%` }} /></div></div>)}</div><button onClick={() => setView("escalations")} className="button-secondary mt-7 w-full">Review escalations →</button></section></div>
    <section className="panel overflow-hidden"><div className="border-b border-slate-100 p-5"><p className="eyebrow">Patients</p><h3 className="mt-1 text-lg font-black text-navy">Test patient records</h3></div><div className="grid divide-y divide-slate-100 md:grid-cols-3 md:divide-x md:divide-y-0">{patients.slice(0, 3).map((patient) => <button key={patient.id} onClick={() => setView("patient")} className="flex items-center gap-3 p-5 text-left hover:bg-slate-50"><div className="flex h-10 w-10 items-center justify-center rounded-full bg-mint font-bold text-teal">{initials(patient.name)}</div><div><p className="text-sm font-bold text-ink">{patient.name}</p><p className="mt-1 text-xs text-slate-500">{patient.case_id}</p></div></button>)}{patients.length === 0 && <EmptyState text="No patients in the test database." />}</div></section>
  </div>;
}

function EmptyState({ text }: { text: string }) {
  return <div className="p-8 text-center text-sm text-slate-500">{text}</div>;
}

function PatientsView({ patients, setView }: { patients: Patient[]; setView: (view: View) => void }) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => patients.filter((patient) => `${patient.name} ${patient.case_id} ${patient.language}`.toLowerCase().includes(query.toLowerCase())), [patients, query]);
  return <div className="space-y-6"><div><p className="text-sm text-slate-500">Synthetic test records only.</p><h2 className="mt-1 text-2xl font-black text-navy">All patients <span className="ml-2 text-base font-bold text-slate-400">{patients.length}</span></h2></div><section className="panel overflow-hidden"><div className="border-b border-slate-100 p-4"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search test patients..." className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal" /></div><div className="overflow-x-auto"><table className="w-full min-w-[700px] text-left"><thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500"><tr><th className="px-5 py-3">Patient</th><th className="px-5 py-3">Language</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Risk</th><th className="px-5 py-3">Follow-up</th></tr></thead><tbody className="divide-y divide-slate-100">{filtered.map((patient) => <tr key={patient.id}><td className="px-5 py-4"><button onClick={() => setView("patient")} className="flex items-center gap-3 text-left"><div className="flex h-9 w-9 items-center justify-center rounded-full bg-mint text-xs font-black text-teal">{initials(patient.name)}</div><div><p className="text-sm font-bold text-ink">{patient.name}</p><p className="text-xs text-slate-400">{patient.case_id}</p></div></button></td><td className="px-5 py-4 text-sm text-slate-600">{patient.language}</td><td className="px-5 py-4"><Badge tone="teal">{patient.status}</Badge></td><td className="px-5 py-4"><Badge tone={patient.risk_level === "high" ? "red" : patient.risk_level === "medium" ? "amber" : "green"}>{patient.risk_level}</Badge></td><td className="px-5 py-4 text-sm text-slate-600">{patient.follow_up}</td></tr>)}</tbody></table>{filtered.length === 0 && <EmptyState text="No patients in the test database." />}</div></section></div>;
}

function PatientDetail({ patient, setView }: { patient: Patient | null; setView: (view: View) => void }) {
  if (!patient) return <EmptyState text="Select a patient from the test database." />;
  return <div className="space-y-6"><button onClick={() => setView("patients")} className="text-sm font-bold text-teal">← Back to patients</button><section className="panel p-6"><div className="flex flex-wrap items-center gap-4"><div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-mint text-xl font-black text-teal">{initials(patient.name)}</div><div className="flex-1"><div className="flex flex-wrap items-center gap-3"><h2 className="text-2xl font-black text-navy">{patient.name}</h2><TestLabel /></div><p className="mt-1 text-sm text-slate-500">{patient.case_id} · {patient.age} years · {patient.language}</p></div></div><div className="mt-6 grid gap-4 border-t border-slate-100 pt-5 sm:grid-cols-2 lg:grid-cols-4"><div><p className="eyebrow">Caregiver</p><p className="mt-1 text-sm font-bold">{patient.caregiver}</p><p className="text-xs text-slate-500">{patient.phone}</p></div><div><p className="eyebrow">Consent</p><p className="mt-1 text-sm font-bold text-emerald-700">✓ {patient.consent}</p></div><div><p className="eyebrow">Next follow-up</p><p className="mt-1 text-sm font-bold">{patient.follow_up}</p></div><div><p className="eyebrow">Risk level</p><Badge tone="green">{patient.risk_level}</Badge></div></div></section><section className="panel p-5"><p className="eyebrow">Recent care</p><h3 className="mt-1 text-lg font-black text-navy">Activity</h3>{patient.activities.length ? patient.activities.map((item) => <div key={item.id} className="mt-4 flex gap-3"><div className="mt-1 h-2 w-2 rounded-full bg-teal" /><div><p className="text-sm font-bold">{item.text}</p><p className="text-xs text-slate-500">{new Date(item.occurred_at).toLocaleString()}</p></div></div>) : <EmptyState text="No activity for this test patient." />}</section></div>;
}

function EscalationsView({ escalations }: { escalations: Escalation[] }) {
  return <div className="space-y-6"><div><p className="text-sm text-slate-500">Synthetic test records only.</p><h2 className="mt-1 text-2xl font-black text-navy">Escalation queue</h2></div><section className="panel p-5">{escalations.length ? escalations.map((item) => <div key={item.id} className="border-b border-slate-100 py-4 last:border-0"><div className="flex justify-between gap-3"><p className="font-bold text-ink">{item.reason}</p><Badge tone={item.risk_level === "high" ? "red" : "amber"}>{item.risk_level}</Badge></div><p className="mt-1 text-xs text-slate-500">{item.status} · {new Date(item.created_at).toLocaleString()}</p></div>) : <EmptyState text="No escalations in the test database." />}</section></div>;
}

export default function Home() {
  const [view, setView] = useState<View>("overview");
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getOverview(), getPatients(), getActivity(), getEscalations()])
      .then(([overviewData, patientData, activityData, escalationData]) => { setOverview(overviewData); setPatients(patientData); setActivity(activityData); setEscalations(escalationData); })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load test data."));
  }, []);

  useEffect(() => {
    if (view === "patient" && patients[0]) getPatient(patients[0].id).then(setSelectedPatient).catch(() => setSelectedPatient(null));
  }, [view, patients]);

  const content = error ? <div className="panel p-8 text-center text-sm text-urgent">{error}</div> : !overview ? <div className="panel p-8 text-center text-sm text-slate-500">Loading TEST DATA...</div> : view === "overview" ? <Overview data={overview} patients={patients} activity={activity} setView={setView} /> : view === "patients" ? <PatientsView patients={patients} setView={setView} /> : view === "patient" ? <PatientDetail patient={selectedPatient} setView={setView} /> : view === "escalations" ? <EscalationsView escalations={escalations} /> : <div className="panel p-8 text-center text-sm text-slate-500">Voice testing is available for the synthetic test patient only.</div>;
  return <div className="min-h-screen bg-[#f7faf9] text-ink"><Sidebar view={view} setView={setView} escalationCount={overview?.pending_escalations ?? 0} /><div className="lg:pl-64"><Header view={view} setView={setView} /><main className="mx-auto max-w-7xl p-5 md:p-8">{content}</main></div></div>;
}
