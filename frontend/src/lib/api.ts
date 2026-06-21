export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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

interface BackendAgentOutput {
  agent_name: string;
  decision: string;
  rationale: string;
  confidence: number;
  signals?: string[];
}

interface BackendTriageResult {
  bug_id?: string | null;
  status: string;
  severity: Severity;
  assigned_team: string;
  confidence: number;
  summary: string;
  explanation: string;
  agent_outputs?: BackendAgentOutput[];
  created_at?: string;
}

interface BackendBug {
  bug_id?: string | null;
  title: string;
  description: string;
  severity_hint?: Severity | null;
  status?: string;
  repository?: string | null;
  labels?: string[];
  created_at?: string;
}

interface BackendMetrics {
  total_bugs: number;
  triaged_bugs: number;
  duplicate_rate: number;
  average_triage_seconds: number;
  severity_breakdown: Partial<Record<Severity, number>>;
}

async function j<T>(p: Promise<Response>): Promise<T> {
  const r = await p;
  if (!r.ok) {
    let detail = `${r.status} ${r.statusText}`;
    try {
      const body = await r.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {
      // Keep the status text when the API does not return JSON.
    }
    throw new Error(detail);
  }
  return r.json() as Promise<T>;
}

function normalizeAgents(outputs: BackendAgentOutput[] = []): AgentStep[] {
  return outputs.map((agent) => ({
    name: agent.agent_name.replaceAll("_", " "),
    output: [
      `Decision: ${agent.decision}`,
      `Confidence: ${Math.round(agent.confidence * 100)}%`,
      agent.rationale,
      agent.signals?.length ? `Signals: ${agent.signals.join(", ")}` : "",
    ]
      .filter(Boolean)
      .join("\n"),
  }));
}

function normalizeTriageResult(result: BackendTriageResult, title: string): TriageResult {
  return {
    id: result.bug_id ?? crypto.randomUUID(),
    title,
    severity: result.severity,
    category: result.assigned_team,
    summary: result.summary,
    suggested_fix: result.explanation,
    agents: normalizeAgents(result.agent_outputs),
    created_at: result.created_at,
  };
}

function normalizeBug(bug: BackendBug): Bug {
  return {
    id: bug.bug_id ?? bug.title,
    title: bug.title,
    severity: bug.severity_hint ?? "medium",
    category: bug.repository ?? bug.status ?? "triage",
    summary: bug.description,
    created_at: bug.created_at,
  };
}

function normalizeMetrics(metrics: BackendMetrics): Metrics {
  const total = metrics.total_bugs ?? 0;
  const triaged = metrics.triaged_bugs ?? 0;
  return {
    total,
    by_severity: {
      critical: metrics.severity_breakdown?.critical ?? 0,
      high: metrics.severity_breakdown?.high ?? 0,
      medium: metrics.severity_breakdown?.medium ?? 0,
      low: metrics.severity_breakdown?.low ?? 0,
    },
    avg_response_ms: Math.round((metrics.average_triage_seconds ?? 0) * 1000),
    resolved: triaged,
    open: Math.max(total - triaged, 0),
  };
}

export const api = {
  triage: async (body: { title: string; description: string }) => {
    const result = await j<BackendTriageResult>(
      fetch(`${API_BASE}/triage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    );
    return normalizeTriageResult(result, body.title);
  },
  bugs: async () => (await j<BackendBug[]>(fetch(`${API_BASE}/bugs`))).map(normalizeBug),
  metrics: async () => normalizeMetrics(await j<BackendMetrics>(fetch(`${API_BASE}/metrics`))),
};

export const severityColor: Record<Severity, string> = {
  critical: "text-coral border-coral",
  high: "text-amber border-amber",
  medium: "text-lime border-lime",
  low: "text-violet border-violet",
};
