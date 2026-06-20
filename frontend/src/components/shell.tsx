import { Link, useRouterState } from "@tanstack/react-router";
import { motion } from "motion/react";
import type { ReactNode } from "react";
import logo from "@/assets/xtriage-logo.png";

function NavLink({ to, label, idx }: { to: string; label: string; idx: string }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const active = pathname === to;
  return (
    <Link to={to} className="group relative px-1 py-2">
      <span className="flex items-baseline gap-2">
        <span className="text-[10px] font-mono text-muted-foreground">{idx}</span>
        <span
          className={`text-sm tracking-tight transition-colors ${
            active ? "text-foreground" : "text-muted-foreground group-hover:text-foreground"
          }`}
        >
          {label}
        </span>
      </span>
      {active && (
        <motion.span
          layoutId="nav-underline"
          className="absolute -bottom-px left-0 right-0 h-px bg-accent"
          transition={{ type: "spring", stiffness: 380, damping: 32 }}
        />
      )}
    </Link>
  );
}

const TickerStrip = () => {
  const items = [
    "v1.0",
    "no-auth",
    "no-persist",
    "local://8000",
    "agents: intake → classify → fix",
    "severity scale: critical · high · medium · low",
    "render only · backend defines schema",
  ];
  const row = [...items, ...items, ...items];
  return (
    <div className="overflow-hidden border-y border-border bg-background/40">
      <div className="marquee flex gap-10 py-2 whitespace-nowrap">
        {row.map((t, i) => (
          <span
            key={i}
            className="flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground"
          >
            <span className="size-1 rounded-full bg-accent" />
            {t}
          </span>
        ))}
      </div>
    </div>
  );
};

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 bg-background/70 backdrop-blur-xl border-b border-border">
        <div className="mx-auto max-w-[920px] px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <span className="relative inline-flex items-center justify-center size-9 rounded-md bg-accent/10 ring-1 ring-accent/30 overflow-hidden">
              <img
                src={logo}
                alt="xTriage logo"
                width={36}
                height={36}
                className="size-7 object-contain transition-transform duration-500 group-hover:rotate-12"
              />
              <span className="absolute -top-0.5 -right-0.5 size-1.5 rounded-full bg-accent live-dot" />
            </span>
            <span className="flex items-baseline gap-0.5">
              <span className="italic-serif text-2xl leading-none text-accent">x</span>
              <span className="font-display text-xl leading-none tracking-tight">Triage</span>
            </span>
            <span className="hidden sm:inline ml-2 text-[10px] font-mono uppercase tracking-[0.28em] text-muted-foreground">
              triage·console
            </span>
          </Link>
          <nav className="flex items-center gap-5">
            <NavLink to="/" label="Triage" idx="01" />
            <NavLink to="/dashboard" label="Metrics" idx="02" />
          </nav>
        </div>
        <TickerStrip />
      </header>

      <main className="mx-auto max-w-[920px] px-6 py-12">{children}</main>

      <footer className="mx-auto max-w-[920px] px-6 py-10 mt-16 border-t border-border">
        <div className="flex items-end justify-between gap-6">
          <div>
            <div className="font-display text-4xl leading-none">
              ship <span className="italic-serif text-accent">cleaner</span>.
            </div>
            <div className="mt-2 text-xs font-mono text-muted-foreground uppercase tracking-[0.22em]">
              © xTriage — built for fast feedback loops
            </div>
          </div>
          <div className="text-right text-[10px] font-mono uppercase tracking-[0.28em] text-muted-foreground">
            api · localhost:8000<br />
            v1.0 · local only
          </div>
        </div>
      </footer>
    </div>
  );
}
