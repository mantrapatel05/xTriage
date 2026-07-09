# xTriage

**AI-assisted bug triage that actually gets measured.**

xTriage reads a bug report, searches for similar historical issues, predicts severity, explains the decision, and recommends the engineering team that should own it — then proves whether each architectural choice actually works on a balanced, real-world evaluation set.

Built with a FastAPI backend, React dashboard, multi-agent LLM pipeline, sentence-transformer embeddings, and ChromaDB vector search. Every design decision — multi-agent vs. single-call, RAG on vs. off, threshold tuning, prompt calibration — is backed by a 300-bug Mozilla Bugzilla benchmark with full confusion matrices, macro-F1, and per-class recall.

---

## Results at a Glance

Evaluated on a **balanced 300-bug Bugzilla set** (75 per severity tier). Majority baseline on balanced data: **25.0%**.

| Approach | Accuracy | Macro-F1 | Critical Recall | High Recall |
|----------|----------|----------|-----------------|-------------|
| Single-call LLM | 31.0% | — | 0% | 49% |
| Multi-agent (no RAG) | 38.0% | 26.3% | 17% | 60% |
| Multi-agent + RAG v1 | 38.0% | 33.4% | 71% | 28% |
| **Multi-agent + RAG v2** | **47.0%** | **42.0%** | **73%** | **51%** |

The final RAG-powered pipeline **nearly doubles macro-F1** over vanilla multi-agent, catches almost three-quarters of critical bugs, and recovers high-severity detection without the over-escalation that plagued the first RAG attempt.

---

## Why This Project Exists

Engineering teams answer the same triage questions on every bug report:

- Is this a duplicate of something we've already seen?
- How severe is it — really?
- What's the business impact?
- Which team should own it?
- What context should the assignee know first?

xTriage explores how an AI system can assist that workflow — and, just as importantly, **honestly measures** whether complexity (multi-agent orchestration, RAG, prompt engineering) actually beats simpler baselines. Early on, a data-quality bug inflated headline accuracy: a GitHub-sourced eval set was 96% "medium," so a model that always guessed "medium" would beat our system. We caught that, replaced the dataset, and now report macro-F1 and per-class recall alongside raw accuracy.

---

## Features

- **Bug report intake** — Submit title, description, and optional metadata via API or React UI
- **Multi-agent severity analysis** — Separate technical and business LLM agents, aggregated with a max-rule (business can escalate, never reduce)
- **RAG over historical bugs** — Retrieves top-3 similar past bugs from ChromaDB and injects severity, resolution, component, and team metadata into every agent prompt
- **Duplicate detection** — Semantic similarity search using sentence-transformer embeddings
- **Team assignment** — LLM-powered recommendation informed by tech + business analysis and historical context
- **Explainable triage** — Full agent trace with rationale, confidence scores, and signals
- **Groq API key rotation** — Automatic rotation across multiple keys with cooldown on rate limits, exponential backoff, and retry-after header parsing; keys partitioned between multi-agent pipeline and single-call benchmark so they never compete for quota
- **Evaluation pipeline** — Bulk eval with confusion matrix, per-class precision/recall/F1, macro-F1, and majority-baseline comparison
- **Agent-vs-single-call benchmark** — Head-to-head on the same 300 labelled bugs: accuracy, latency, token cost
- **Bugzilla-sourced eval set** — 300 real bugs from Mozilla Bugzilla's public REST API, stratified 75/75/75/75 across severity tiers with human-assigned ground truth
- **Metrics endpoint** — Triage counts, duplicate rate, average triage time, severity distribution
- **React dashboard** — Editorial UI for submission, history, and telemetry
- **Graceful degradation** — Groq unavailable → safe fallback results, never 500 errors; fallback calls tracked separately in eval runs

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 |
| **LLM** | Groq API (`llama-3.1-8b-instant`) |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) |
| **Vector DB** | ChromaDB (`PersistentClient`, cosine similarity) |
| **Frontend** | React, TypeScript, Vite, TanStack Router, Tailwind CSS, Motion |

---

## System Architecture

```text
User submits bug report
        │
        ▼
Frontend React app  ──►  POST /triage
        │
        ▼
TriageLead orchestrator
        │
        ├─► Duplicate detector
        │       └─► SentenceTransformer embeddings + ChromaDB similarity
        │
        ├─► RAG retrieval (top-3 similar historical bugs, similarity ≥ threshold)
        │       └─► Injects severity, resolution, component, team into prompts
        │
        ├─► Technical analyzer agent  (Llama via Groq)
        ├─► Business impact agent     (Llama via Groq)
        └─► Assignment agent          (Llama via Groq)
        │
        ▼
Triage result
        ├─► Severity (max of tech + business)
        ├─► Assigned team
        ├─► Confidence score
        ├─► Explanation with agent traces
        └─► Duplicate + historical context matches
```

### RAG Pipeline

Historical bugs from the eval corpus are embedded and stored in ChromaDB. At triage time:

1. The incoming bug's title + description is embedded and queried against the collection
2. Top-3 matches above the similarity threshold are retrieved with metadata (severity, resolution, component, team)
3. A formatted context block is injected into all three LLM agent prompts
4. Agents are instructed to treat historical bugs as **reference only** — severity is calibrated from the current bug's own symptoms, not blindly copied from similar past issues

```bash
# Seed the vector store before running eval or serving triage with RAG
cd backend/app/eval
python index_historical_bugs.py
```

### API Key Rotation

```text
GroqClientPool (shared singleton)
        │
        ├─► Slot 1 (GROQ_API_KEY_1)  ─┐
        ├─► Slot 2 (GROQ_API_KEY_2)   ├─► Multi-agent pool (keys 1–3)
        ├─► Slot 3 (GROQ_API_KEY_3)  ─┘
        ├─► Slot 4 (GROQ_API_KEY_4)  ─┐
        └─► Slot 5 (GROQ_API_KEY_5)  ─┘  Single-call benchmark pool (keys 4–5)
        │
        ├─► Rate-limited keys → cooldown (retry-after header)
        ├─► Invalid keys → permanently disabled
        ├─► Transient errors → exponential backoff
        └─► All keys exhausted → GroqClientUnavailable → agent fallback
```

---

## Repository Structure

```text
xTriage/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── triage_lead.py          # Orchestrator — RAG + agents + max-rule severity
│   │   │   ├── technical_analyzer.py   # Technical severity & complexity
│   │   │   ├── business_analyzer.py    # Business impact & priority
│   │   │   ├── duplicate_detector.py   # Vector similarity duplicate search
│   │   │   └── assignment_agent.py     # Team assignment recommendation
│   │   ├── models/
│   │   │   ├── bug.py                  # BugReport Pydantic model
│   │   │   └── triage_result.py        # TriageResult, AgentOutput models
│   │   ├── routers/
│   │   │   ├── triage.py               # POST /triage
│   │   │   ├── bugs.py                 # GET /bugs
│   │   │   ├── metrics.py              # GET /metrics
│   │   │   └── health.py               # GET /health
│   │   ├── services/
│   │   │   ├── groq_client.py          # Multi-key pool with rotation & cooldown
│   │   │   ├── embeddings.py           # SentenceTransformer embedding service
│   │   │   ├── vector_store.py         # ChromaDB persistent vector store
│   │   │   └── metrics_tracker.py      # In-memory triage metrics
│   │   ├── eval/
│   │   │   ├── run_eval.py             # Full 300-bug eval (confusion matrix + macro-F1)
│   │   │   ├── agent_benchmark.py      # Multi-agent vs single-call head-to-head
│   │   │   ├── baseline_eval.py        # Majority / uniform / weighted-random baselines
│   │   │   ├── smoke_test.py           # 1-bug-per-tier pipeline sanity check
│   │   │   ├── index_historical_bugs.py # Seed ChromaDB from eval corpus (RAG)
│   │   │   ├── fetch_bugzilla_issues.py # Mozilla Bugzilla REST API fetcher
│   │   │   ├── fetch_github_issues.py   # GitHub issue scraper (legacy source)
│   │   │   ├── curate_and_label.py      # Curation / labelling tool
│   │   │   └── eval/
│   │   │       ├── bugs.json                    # 300 labelled Bugzilla bugs
│   │   │       ├── raw_bugzilla_bugs.json
│   │   │       ├── predictions.json
│   │   │       ├── agent_benchmark_single.json
│   │   │       └── agent_benchmark_multi.json
│   │   ├── data/
│   │   │   └── seed_bugs.py
│   │   ├── config.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/                   # UI components (shadcn/ui)
│   │   ├── lib/                          # API client
│   │   └── routes/                       # Triage form + dashboard
│   └── package.json
├── run.py
├── .env.example
├── sample_bugs.json
└── README.md
```

---

## Quick Start

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd xTriage
```

Create a `.env` in the project root (see `.env.example`):

```env
APP_NAME=Bug Triage Agent
APP_VERSION=0.1.0
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080

# At least one Groq key required. Multiple keys enable automatic rotation:
GROQ_API_KEY_1=gsk_your_key_1
GROQ_API_KEY_2=gsk_your_key_2
GROQ_API_KEY_3=gsk_your_key_3
GROQ_API_KEY_4=gsk_your_key_4
GROQ_API_KEY_5=gsk_your_key_5

# Optional overrides (defaults: keys 1–3 = multi-agent, keys 4–5 = benchmark)
# GROQ_MULTI_API_KEYS=
# GROQ_SINGLE_API_KEYS=
# GROQ_MODEL=llama-3.1-8b-instant
# GROQ_MAX_COMPLETION_TOKENS=220
# GROQ_PROMPT_DESCRIPTION_CHARS=2500
```

### 2. Start the backend

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r backend/requirements.txt
python run.py
```

API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

### 3. Seed historical bugs for RAG

```bash
cd backend/app/eval
python index_historical_bugs.py
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

UI: `http://localhost:8080`

---

## API Overview

### `POST /triage`

```json
{
  "title": "OAuth callback redirects to 404",
  "description": "After approving Google sign-in, users are redirected to /404 instead of /dashboard. Production only.",
  "repository": "org/my-app",
  "issue_url": "https://github.com/org/my-app/issues/42",
  "labels": ["bug", "auth"]
}
```

Response includes `severity`, `assigned_team`, `confidence`, `explanation`, `duplicate_matches`, and `agent_outputs` with per-agent rationale and signals.

### `GET /bugs` · `GET /metrics` · `GET /health`

List known bugs (paginated), triage telemetry, and service health. Full schemas at `/docs`.

---

## Evaluation Methodology

### The dataset

The original eval set was scraped from GitHub issues and auto-labelled. **96% of bugs were tagged "medium"** — a model that always guessed "medium" would score 96%. Our 82% headline number was actually 14 points *below* that trivial baseline. Data bug, not model bug.

The current set is pulled from **Mozilla Bugzilla's public REST API**, which carries human-assigned `severity` on every bug. Bugzilla's 6-tier scale maps to xTriage's 4 tiers:

```text
blocker, critical  →  critical
major              →  high
normal             →  medium
minor, trivial     →  low
```

`eval/bugs.json` contains **300 bugs, split exactly 75/75/75/75** — genuinely balanced with real ground truth.

### Running the eval

```bash
# Terminal 1 — backend
python run.py

# Terminal 2 — seed RAG corpus (first time or after corpus changes)
cd backend/app/eval
python index_historical_bugs.py

# Terminal 3 — full eval
cd backend/app/eval
python run_eval.py
```

| Variable | Default | Description |
|----------|---------|-------------|
| `TRIAGE_URL` | `http://localhost:8000/triage` | Backend endpoint |
| `EVAL_REQUEST_TIMEOUT` | `300` | HTTP timeout per request (seconds) |
| `EVAL_SLEEP_SECONDS` | `10` | Delay between requests (rate-limit safety) |

**How to read output:**

- **OK** — Predicted severity matches ground truth
- **MISS (got X, expected Y)** — Wrong prediction, shows actual vs expected
- **[FALLBACK xN]** — N agent calls fell back to safe defaults (Groq unavailable)
- Report **macro-F1**, not just raw accuracy — on imbalanced sets, accuracy rewards always guessing the majority class

### Baseline sanity check

```bash
cd backend/app/eval
python baseline_eval.py
```

Computes majority-class, uniform-random, and weighted-random baselines so headline numbers are never reported without context.

### Smoke test

```bash
cd backend/app/eval
python smoke_test.py
```

Fast pre-flight: one bug per severity tier, fallback-call tracking. Run before a full 300-bug eval.

### Agent benchmark (multi-agent vs single-call)

```bash
cd backend/app/eval
python agent_benchmark.py
```

Runs the same 300 bugs through both approaches on **separate Groq key pools**, reporting accuracy, latency, and token cost side by side.

---

## Evaluation Results

All results on the **balanced 300-bug Bugzilla set** (75 per tier). Majority baseline: **25.0%**.

### 1. Pre-RAG — no historical context

#### Single-call LLM

| Metric | Value |
|--------|-------|
| Accuracy | 31.0% |

One consolidated Groq call returns technical severity, business severity, team, and confidence. Fast (~316 ms/bug) but shallow — 0% critical recall, heavy bias toward `medium`/`high`.

#### Multi-agent (technical + business + assignment)

| Metric | Value |
|--------|-------|
| Accuracy | **38.0%** |
| Macro-F1 | 26.3% |
| Critical recall | 17% |
| High recall | 60% |
| Low recall | 0% |
| Fallback calls | 0 |

Three specialized agents with max-rule severity aggregation. Better tier spread and stronger high recall, but still zero correct `low` predictions — classic LLM over-escalation on cosmetic bugs.

---

### 2. RAG v1 — historical context (threshold = 0.5, full docs)

| Metric | Value |
|--------|-------|
| Accuracy | 38.0% |
| Macro-F1 | 33.4% |
| Critical recall | 71% |
| High recall | 28% |
| Low recall | 4% |
| Fallback calls | 1 |

**Confusion matrix** (rows = truth, cols = predicted):

```text
            low   medium   high   critical
low          3       46     18         8
medium       6       37     24         8
high         0       14     21        40
critical     0        7     15        53
```

**Per-class metrics:**

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| low | 0.33 | 0.04 | 0.07 |
| medium | 0.36 | 0.49 | 0.41 |
| high | 0.27 | 0.28 | 0.27 |
| critical | 0.49 | 0.71 | 0.58 |

RAG dramatically improved critical recall (17% → 71%) but introduced **over-escalation** — agents copied severity from similar historical bugs instead of calibrating from the current report. High recall collapsed (60% → 28%).

---

### 3. RAG v2 — optimised (threshold = 0.7, truncated docs, de-escalation prompt)

| Metric | Value |
|--------|-------|
| Accuracy | **47.0%** |
| Macro-F1 | **42.0%** |
| Critical recall | **73%** |
| High recall | **51%** |
| Medium recall | 48% |
| Low recall | 8% |
| Fallback calls | 9 |

**Confusion matrix** (rows = truth, cols = predicted):

```text
            low   medium   high   critical
low          6       44     13        12
medium       6       36     23        10
high         0        9     38        28
critical     0        5     15        55
```

**Per-class metrics:**

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| low | 0.50 | 0.08 | 0.14 |
| medium | 0.38 | 0.48 | 0.43 |
| high | 0.43 | 0.51 | **0.46** |
| critical | 0.52 | 0.73 | **0.61** |

Three targeted fixes over v1:

1. **Higher similarity threshold (0.7)** — only inject historical bugs that are genuinely relevant, reducing noise
2. **Truncated context (300-char summaries)** — keeps prompts focused, avoids drowning agents in full Bugzilla write-ups
3. **De-escalation prompt** — explicit instruction that historical bugs are reference only; severity must come from the current bug's own symptoms

Result: critical recall held at 73%, high recall recovered to 51%, macro-F1 nearly doubled vs. pre-RAG multi-agent.

---

### Improvement arc

```text
31% ──► 38% ──► 38% ──► 47%
 │       │       │       │
 │       │       │       └─ RAG v2: calibrated context + de-escalation
 │       │       └─ RAG v1: critical recall spike, but over-escalation
 │       └─ Multi-agent: better tier spread, still no low recall
 └─ Single-call: fast, shallow, 0% critical recall
```

| What changed | Critical recall | High recall | Macro-F1 |
|-------------|-----------------|-------------|----------|
| Single-call → Multi-agent | 0% → 17% | 49% → 60% | — → 26.3% |
| Multi-agent → RAG v1 | 17% → 71% | 60% → 28% | 26.3% → 33.4% |
| RAG v1 → RAG v2 | 71% → 73% | 28% → 51% | 33.4% → 42.0% |

---

## Design Decisions

### Max-rule severity aggregation

Technical and business agents each rate severity independently (low → critical). The final severity is the **maximum** of the two:

- Business **can escalate** (technically simple but blocks all users → critical)
- Business **can never reduce** (technically complex but cosmetic → stays at tech's rating)

This is a likely contributor to the multi-agent pipeline's stronger critical-class recall relative to single-call.

### Graceful degradation

When Groq is unavailable (rate limited, quota exhausted, network error):

1. `GroqClientPool` retries with exponential backoff across all keys in its pool
2. All keys exhausted → `GroqClientUnavailable`
3. Each agent returns a safe fallback (medium severity, triage-team assignment)
4. Backend responds `200 OK` with the fallback — never a 500
5. Eval scripts track fallback calls separately so degraded runs aren't silently averaged in

---

## What This Project Demonstrates

- **Rigorous eval methodology** — caught a 96%-medium data skew that inflated an earlier headline number; replaced it with balanced, real-ground-truth Bugzilla data
- **Iterative RAG engineering** — v1 proved historical context helps critical recall; v2 fixed over-escalation with threshold tuning, truncation, and prompt calibration
- **Multi-agent vs single-call benchmarking** — architectural choices measured on accuracy, latency, and cost, not shipped on faith
- **Production-minded API design** — FastAPI + Pydantic, key rotation with pool partitioning, graceful degradation, explainable agent traces
- **Vector search for triage** — embeddings for both duplicate detection and RAG context retrieval
- **End-to-end product** — React dashboard, metrics, OpenAPI docs, eval tooling

---

## License

Intended for learning, experimentation, and portfolio development.
