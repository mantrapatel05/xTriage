import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Shell } from "@/components/shell";
import { api, type Bug, type Metrics, type Severity } from "@/lib/api";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Metrics // xTriage" },
      { name: "description", content: "Live metrics and triage history." },
    ],
  }),
  component: Dashboard,
});

const sevDot: Record<Severity, string> = {
  critical: "bg-coral",
  high: "bg-flame",
  medium: "bg-amber",
  low: "bg-teal",
};
const sevText: Record<Severity, string> = {
  critical: "text-coral",
  high: "text-flame",
  medium: "text-amber",
  low: "text-teal",
};

function Dashboard() {
  const [m, setM] = useState<Metrics | null>(null);
  const [bugs, setBugs] = useState<Bug[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [mm, bb] = await Promise.all([api.metrics(), api.bugs()]);
        if (!alive) return;
        setM(mm);
        setBugs(bb);
      } catch (e: any) {
        if (alive) setErr(e.message ?? "failed");
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const total = m?.total ?? 0;
  const sevBreakdown: { key: Severity; v: number }[] = [
    { key: "critical", v: m?.by_severity?.critical ?? 0 },
    { key: "high",     v: m?.by_severity?.high ?? 0 },
    { key: "medium",   v: m?.by_severity?.medium ?? 0 },
    { key: "low",      v: m?.by_severity?.low ?? 0 },
  ];

  return (
    <Shell>
      <motion.section
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="mb-12"
      >
        <div className="flex items-center gap-3 text-[10px] font-mono uppercase tracking-[0.32em] text-muted-foreground mb-5">
          <span className="hairline h-px w-10" />
          chapter 02 · telemetry
        </div>
        <h1 className="font-display text-[clamp(2.6rem,7vw,5rem)] leading-[0.95] tracking-[-0.03em]">
          The <span className="italic-serif text-accent">pulse</span> of your backlog,
          <br />measured in milliseconds.
        </h1>
      </motion.section>

      {err && (
        <div className="mb-6 panel border-coral/60 bg-coral/5 p-4 text-sm text-coral font-mono">
          ✕ {err}
        </div>
      )}

      {/* Headline number + severity breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.05 }}
          className="paper-block rounded-md p-6 ring-soft md:col-span-1"
        >
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-ink/60">
            total triaged
          </div>
          <div className="font-display text-[6.5rem] leading-none mt-2 text-ink number-tabular">
            {m ? total : <span className="opacity-30">—</span>}
          </div>
          <div className="mt-3 text-xs font-mono uppercase tracking-[0.22em] text-ink/60">
            since session start
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.12 }}
          className="panel p-6 md:col-span-2"
        >
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground mb-5">
            by severity
          </div>
          <ul className="space-y-3">
            {sevBreakdown.map(({ key, v }) => {
              const pct = total ? (v / total) * 100 : 0;
              return (
                <li key={key} className="grid grid-cols-[80px_1fr_50px] items-center gap-4">
                  <span className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.2em]">
                    <span className={`size-1.5 rounded-full ${sevDot[key]}`} />
                    <span className={sevText[key]}>{key}</span>
                  </span>
                  <span className="relative h-1.5 bg-surface-2 overflow-hidden rounded-full">
                    <motion.span
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
                      className={`absolute inset-y-0 left-0 ${sevDot[key]}`}
                    />
                  </span>
                  <span className="text-right font-mono text-sm number-tabular">{v}</span>
                </li>
              );
            })}
          </ul>
        </motion.div>
      </div>

      {/* Secondary metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-12">
        <SmallStat label="open" value={m?.open} />
        <SmallStat label="resolved" value={m?.resolved} accent />
        <SmallStat label="avg latency" value={m?.avg_response_ms} suffix="ms" />
      </div>

      {/* History */}
      <section className="panel overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface-2/40">
          <span className="font-mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
            GET · /bugs · history
          </span>
          <span className="font-mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground number-tabular">
            {bugs ? `${bugs.length} entries` : "—"}
          </span>
        </div>

        {!bugs && !err && (
          <ul className="divide-y divide-border">
            {Array.from({ length: 4 }).map((_, i) => (
              <li key={i} className="px-5 py-4 flex items-center gap-4">
                <span className="size-2 rounded-full skeleton" />
                <span className="h-3 flex-1 skeleton rounded-full" />
                <span className="h-3 w-16 skeleton rounded-full" />
              </li>
            ))}
          </ul>
        )}

        {bugs && bugs.length === 0 && (
          <div className="p-16 text-center">
            <div className="font-display italic-serif text-3xl text-muted-foreground">
              the silence is suspicious
            </div>
            <div className="mt-2 text-xs font-mono uppercase tracking-[0.22em] text-muted-foreground">
              no bugs logged yet — triage one to populate
            </div>
          </div>
        )}

        {bugs && bugs.length > 0 && (
          <ul className="divide-y divide-border">
            {bugs.map((b, i) => (
              <motion.li
                key={b.id}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: Math.min(i, 8) * 0.04 }}
                className="px-5 py-4 grid grid-cols-[16px_64px_1fr_auto] items-center gap-4 hover:bg-surface-2/40 transition-colors"
              >
                <span className={`size-2 rounded-full ${sevDot[b.severity]}`} />
                <span className="font-mono text-[10px] text-muted-foreground number-tabular">
                  #{String(b.id).slice(0, 6)}
                </span>
                <span className="truncate font-display text-base">{b.title}</span>
                <span className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase tracking-[0.22em] text-muted-foreground">
                    {b.category}
                  </span>
                  <span className={`text-[10px] font-mono uppercase tracking-[0.22em] ${sevText[b.severity]}`}>
                    {b.severity}
                  </span>
                </span>
              </motion.li>
            ))}
          </ul>
        )}
      </section>
    </Shell>
  );
}

function SmallStat({
  label,
  value,
  suffix,
  accent,
}: {
  label: string;
  value: number | undefined;
  suffix?: string;
  accent?: boolean;
}) {
  return (
    <div className={`panel p-5 ${accent ? "border-accent/40" : ""}`}>
      <div className="text-[10px] font-mono uppercase tracking-[0.28em] text-muted-foreground">
        {label}
      </div>
      <div className={`mt-3 font-display text-4xl leading-none number-tabular ${accent ? "text-accent" : ""}`}>
        {value ?? <span className="opacity-30">—</span>}
        {suffix && value !== undefined && (
          <span className="ml-1.5 text-xs font-mono text-muted-foreground">{suffix}</span>
        )}
      </div>
    </div>
  );
}
