export const API_BASE = "http://localhost:8000";

export type Severity = "critical" | "high" | "medium" | "low";

export interface AgentStep {
  name: string;
  output: string;
}

export interface TriageResult {
  id: string;
  title: string;
  severity: Severity;
  category: string;
  summary: string;
  suggested_fix?: string;
  agents?: AgentStep[];
  created_at?: string;
}

export interface Bug extends TriageResult {}

export interface Metrics {
  total: number;
  by_severity: Record<Severity, number>;
  avg_response_ms?: number;
  resolved?: number;
  open?: number;
}

async function j<T>(p: Promise<Response>): Promise<T> {
  const r = await p;
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

export const api = {
  triage: (body: { title: string; description: string }) =>
    j<TriageResult>(
      fetch(`${API_BASE}/triage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    ),
  bugs: () => j<Bug[]>(fetch(`${API_BASE}/bugs`)),
  metrics: () => j<Metrics>(fetch(`${API_BASE}/metrics`)),
};

export const severityColor: Record<Severity, string> = {
  critical: "text-coral border-coral",
  high: "text-amber border-amber",
  medium: "text-lime border-lime",
  low: "text-violet border-violet",
};
