import { createFileRoute } from "@tanstack/react-router";
import { useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Shell } from "@/components/shell";
import { api, type TriageResult, type Severity } from "@/lib/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Triage // xTriage" },
      { name: "description", content: "Submit a bug, get an AI triage verdict in seconds." },
    ],
  }),
  component: Home,
});

const sevMeta: Record<Severity, { dot: string; label: string; text: string; bg: string }> = {
  critical: { dot: "bg-coral", label: "Critical", text: "text-coral", bg: "bg-coral/10" },
  high:     { dot: "bg-flame", label: "High",     text: "text-flame", bg: "bg-flame/10" },
  medium:   { dot: "bg-amber", label: "Medium",   text: "text-amber", bg: "bg-amber/10" },
  low:      { dot: "bg-teal",  label: "Low",      text: "text-teal",  bg: "bg-teal/10" },
};

function Home() {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    setResult(null);
    try {
      const r = await api.triage({ title, description: desc });
      setResult(r);
    } catch (e: any) {
      setErr(e.message ?? "request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Shell>
      {/* Hero */}
      <motion.section
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="mb-14"
      >
        <div className="flex items-center gap-3 text-[10px] font-mono uppercase tracking-[0.32em] text-muted-foreground mb-5">
          <span className="hairline h-px w-10" />
          chapter 01 · intake
        </div>
        <h1 className="font-display text-[clamp(3rem,9vw,6.5rem)] leading-[0.92] tracking-[-0.03em]">
          Paste the bug.
          <br />
          <span className="italic-serif text-accent">We'll do the </span>
          <span className="italic-serif">thinking</span>
          <span className="caret" />
        </h1>
        <p className="mt-6 max-w-xl text-base text-muted-foreground leading-relaxed">
          A small chorus of agents reads your report, debates severity,
          finds the closest known pattern, and drafts a fix —{" "}
          <span className="text-foreground italic-serif">all before your coffee cools.</span>
        </p>
      </motion.section>

      {/* Form */}
      <motion.form
        onSubmit={submit}
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
        className="panel ring-soft overflow-hidden"
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface-2/40">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-coral/80" />
            <span className="size-2 rounded-full bg-amber/80" />
            <span className="size-2 rounded-full bg-teal/80" />
          </div>
          <span className="font-mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
            POST · /triage
          </span>
        </div>

        <div className="p-6 space-y-6">
          <Field label="Title" hint="one-liner — what broke">
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="OAuth callback redirects to /404"
              className="w-full bg-transparent border-0 border-b border-border focus:border-accent outline-none py-2 text-lg placeholder:text-muted-foreground/50 transition-colors"
            />
          </Field>

          <Field label="Description" hint="repro steps · expected · actual · env">
            <textarea
              required
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows={7}
              placeholder="1. Click Sign in with Google&#10;2. Approve consent&#10;3. Returns to /404 instead of /dashboard&#10;&#10;Expected: lands on /dashboard&#10;Env: Chrome 124, prod"
              className="w-full bg-background/60 border border-border focus:border-accent outline-none p-4 font-mono text-sm leading-relaxed resize-y rounded-sm placeholder:text-muted-foreground/40 transition-colors"
            />
          </Field>

          <div className="flex items-center justify-between pt-2">
            <div className="text-[10px] font-mono uppercase tracking-[0.28em] text-muted-foreground">
              {loading ? (
                <span className="inline-flex items-center gap-2">
                  <span className="size-1.5 rounded-full bg-accent live-dot" />
                  agents · in session
                </span>
              ) : (
                "ready · enter to dispatch"
              )}
            </div>
            <motion.button
              type="submit"
              disabled={loading || !title || !desc}
              whileHover={{ x: -2, y: -2 }}
              whileTap={{ x: 0, y: 0 }}
              transition={{ type: "spring", stiffness: 500, damping: 20 }}
              className="group relative inline-flex items-center gap-3 px-6 py-3 bg-accent text-accent-foreground font-mono text-xs uppercase tracking-[0.22em] font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ boxShadow: "5px 5px 0 0 var(--color-foreground)" }}
            >
              <span>{loading ? "triaging" : "dispatch"}</span>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="transition-transform group-hover:translate-x-1">
                <path d="M2 7h10M7 2l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
              </svg>
            </motion.button>
          </div>
        </div>
      </motion.form>

      <AnimatePresence mode="wait">
        {err && (
          <motion.div
            key="err"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-6 panel border-coral/60 bg-coral/5 p-4 text-sm text-coral flex items-center gap-3"
          >
            <span className="size-1.5 rounded-full bg-coral" />
            <span className="font-mono">{err}</span>
          </motion.div>
        )}

        {loading && <LoadingChorus key="load" />}

        {result && !loading && <ResultCard key="result" r={result} />}
      </AnimatePresence>
    </Shell>
  );
}

function Field({
  label,
  hint,
  children,
}: { label: string; hint: string; children: ReactNode }) {
  return (
    <label className="block group">
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-xs font-mono uppercase tracking-[0.24em] text-foreground/80">
          {label}
        </span>
        <span className="text-[10px] font-mono uppercase tracking-[0.22em] text-muted-foreground">
          {hint}
        </span>
      </div>
      {children}
    </label>
  );
}

function LoadingChorus() {
  const steps = [
    "Intake agent · parsing report",
    "Pattern scout · scanning history",
    "Classifier · voting on severity",
    "Author · drafting suggested fix",
  ];
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="mt-8 panel p-6"
    >
      <div className="text-[10px] font-mono uppercase tracking-[0.28em] text-muted-foreground mb-4">
        chorus · {steps.length} agents
      </div>
      <ul className="space-y-2.5">
        {steps.map((s, i) => (
          <motion.li
            key={s}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.18 }}
            className="flex items-center gap-3 text-sm"
          >
            <span className="font-mono text-[10px] text-muted-foreground w-6">
              {String(i + 1).padStart(2, "0")}
            </span>
            <span className="h-px flex-1 skeleton max-w-[60%]" style={{ animationDelay: `${i * 0.2}s` }} />
            <span className="text-muted-foreground font-mono text-xs">{s}</span>
          </motion.li>
        ))}
      </ul>
    </motion.div>
  );
}



function ResultCard({ r }: { r: TriageResult }) {
  const meta = sevMeta[r.severity];
  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="mt-10"
    >
      {/* Verdict masthead */}
      <div className="paper-block rounded-md p-7 ring-soft relative overflow-hidden">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-[0.3em] text-ink/60 mb-5">
          <span>verdict · #{String(r.id).slice(0, 6)}</span>
          <span>{new Date(r.created_at ?? Date.now()).toLocaleTimeString()}</span>
        </div>
        <h2 className="font-display text-4xl md:text-5xl leading-[1.02] text-ink">
          {r.title}
        </h2>
        <div className="mt-5 flex flex-wrap items-center gap-2">
          <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${meta.bg} ${meta.text} text-xs font-mono uppercase tracking-[0.2em]`}>
            <span className={`size-1.5 rounded-full ${meta.dot}`} />
            {meta.label}
          </span>
          <span className="px-3 py-1.5 rounded-full bg-ink/5 text-ink/80 text-xs font-mono uppercase tracking-[0.2em]">
            # {r.category}
          </span>
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 panel p-6">
        <div className="text-[10px] font-mono uppercase tracking-[0.28em] text-muted-foreground mb-3">
          summary
        </div>
        <p className="text-[17px] leading-relaxed font-display">
          {r.summary}
        </p>
      </div>

      {/* Fix */}
      {r.suggested_fix && (
        <div className="mt-3 panel p-6 border-accent/40">
          <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.28em] text-accent mb-3">
            <span className="size-1.5 rounded-full bg-accent" />
            suggested fix
          </div>
          <pre className="text-xs leading-relaxed whitespace-pre-wrap font-mono text-foreground/90">
{r.suggested_fix}
          </pre>
        </div>
      )}

      {/* Agent trace */}
      {r.agents && r.agents.length > 0 && (
        <div className="mt-3 panel overflow-hidden">
          <div className="px-6 py-3 border-b border-border text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground">
            agent trace · {r.agents.length} steps
          </div>
          <div className="divide-y divide-border">
            {r.agents.map((a, i) => (
              <AgentRow key={i} index={i} name={a.name} output={a.output} />
            ))}
          </div>
        </div>
      )}
    </motion.article>
  );
}

function AgentRow({ index, name, output }: { index: number; name: string; output: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-4 px-6 py-4 hover:bg-surface-2/50 transition-colors text-left"
      >
        <span className="flex items-center gap-4">
          <span className="font-mono text-[10px] text-muted-foreground number-tabular">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="font-display text-lg">{name}</span>
        </span>
        <motion.span
          animate={{ rotate: open ? 90 : 0 }}
          transition={{ type: "spring", stiffness: 400, damping: 28 }}
          className="text-muted-foreground"
        >
          ▸
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <pre className="mx-6 mb-5 ml-[3.25rem] text-xs leading-relaxed whitespace-pre-wrap font-mono text-muted-foreground border-l-2 border-accent/40 pl-4">
{output}
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
