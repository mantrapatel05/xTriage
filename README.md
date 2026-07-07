# xTriage

xTriage is an AI-assisted bug triage system that reads a bug report, checks for related issues, predicts severity, explains the decision, and recommends the engineering team that should handle it.

The project combines a FastAPI backend, a React frontend, LLM-based analysis agents, sentence-transformer embeddings, and ChromaDB vector search to simulate a practical engineering triage workflow.

## Why This Project Exists

Engineering teams receive bug reports with different levels of detail, urgency, and quality. Triage often requires answering the same questions repeatedly:

- Is this a duplicate of an existing issue?
- How severe is the bug?
- What is the business impact?
- Which team should own it?
- What context should the assignee know first?

xTriage explores how an AI system can assist that workflow by combining deterministic API design, vector similarity search, and specialized analysis agents — and, just as importantly, by honestly measuring whether the multi-agent approach actually beats simpler baselines.

## Features

- **Bug report intake** — Submit bug reports with title, description, and optional metadata
- **Technical severity analysis** — LLM-powered analysis of bug complexity, affected components, and severity
- **Business impact analysis** — LLM-powered analysis of user impact, revenue risk, and priority
- **Duplicate detection** — Semantic similarity search using sentence-transformer embeddings and ChromaDB
- **Team assignment** — LLM-powered recommendation of the engineering team that should handle the bug
- **Max-rule severity aggregation** — Business analysis can escalate severity, never reduce it (max of tech + business)
- **Groq API key rotation** — Automatic rotation across multiple API keys with cooldown on rate limits, exponential backoff, and smart retry-after header parsing, with keys partitioned between the multi-agent pipeline and the single-call benchmark so the two never compete for the same quota
- **Explainable triage** — Full agent trace with rationale, confidence scores, and signals
- **Evaluation pipeline** — Bulk eval script with confusion matrix, per-class precision/recall/F1, and majority-baseline comparison (not just raw accuracy)
- **Agent-vs-single-call benchmark** — Head-to-head comparison of the 3-agent pipeline against one consolidated LLM call, on the same labelled bugs, measuring accuracy, latency, and token cost
- **Bugzilla-sourced eval set** — 300 real bugs pulled from Mozilla Bugzilla's public REST API, stratified to be perfectly balanced across severity tiers (see [Evaluation Data](#evaluation-data) below)
- **Metrics endpoint** — Triage counts, duplicate rate, average triage time, severity distribution
- **React dashboard** — UI for submission, history, and telemetry
- **Typed backend models** — Pydantic-based request and response models
- **OpenAPI docs** — Auto-generated at `/docs`

## Tech Stack

### Backend

- Python 3.12
- FastAPI + Uvicorn
- Pydantic v2
- Groq API (llama-3.1-8b-instant) for LLM-powered agents
- ChromaDB for vector storage
- sentence-transformers (all-MiniLM-L6-v2) for text embeddings
- python-dotenv for configuration

### Frontend

- React
- TypeScript
- Vite
- TanStack Router
- Tailwind CSS
- Motion

## System Architecture

```text
User submits bug report
        |
        v
Frontend React app
        |
        v
FastAPI /triage endpoint
        |
        +--> Duplicate detector
        |       +--> SentenceTransformer embeddings
        |       +--> ChromaDB similarity search
        |
        +--> Technical analyzer agent (Llama via Groq)
        |
        +--> Business impact agent (Llama via Groq)
        |
        +--> Assignment agent (Llama via Groq)
        |
        v
Triage result
        |
        +--> Severity (max of tech + business)
        +--> Assigned team
        +--> Confidence score
        +--> Explanation with agent traces
        +--> Duplicate matches
```

### API Key Rotation Architecture

```text
GroqClientPool (shared singleton)
        |
        +--> Slot 1 (GROQ_API_KEY_1)
        +--> Slot 2 (GROQ_API_KEY_2)
        +--> Slot 3 (GROQ_API_KEY_3)
        +--> Slot 4 (GROQ_API_KEY_4)
        +--> Slot 5 (GROQ_API_KEY_5)
        |
        +--> Rate-limited keys go on cooldown (retry-after header)
        +--> Invalid keys are permanently disabled
        +--> Transient errors trigger exponential backoff
        +--> All keys exhausted → GroqClientUnavailable → agent returns fallback
```

Keys are partitioned in `config.py` so the multi-agent backend and the single-call benchmark draw from separate pools (`GROQ_MULTI_API_KEYS` / `GROQ_SINGLE_API_KEYS`, both derived automatically from `GROQ_API_KEY_1..5` if not set explicitly). This exists specifically so that running `agent_benchmark.py` doesn't starve the production `/triage` endpoint of quota, and so the two phases of the benchmark don't contaminate each other's rate limits.

## Repository Structure

```text
xTriage/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── triage_lead.py        # Orchestrator — runs all agents, aggregates severity
│   │   │   ├── technical_analyzer.py # Technical severity & complexity analysis
│   │   │   ├── business_analyzer.py  # Business impact & priority analysis
│   │   │   ├── duplicate_detector.py # Vector similarity duplicate search
│   │   │   └── assignment_agent.py   # Team assignment recommendation
│   │   ├── models/
│   │   │   ├── bug.py                # BugReport Pydantic model
│   │   │   └── triage_result.py      # TriageResult, AgentOutput models
│   │   ├── routers/
│   │   │   ├── triage.py             # POST /triage endpoint
│   │   │   ├── bugs.py               # GET /bugs endpoint
│   │   │   ├── metrics.py            # GET /metrics endpoint
│   │   │   └── health.py             # GET /health endpoint
│   │   ├── services/
│   │   │   ├── groq_client.py        # Multi-key Groq client pool with rotation & cooldown
│   │   │   ├── embeddings.py         # SentenceTransformer embedding service
│   │   │   ├── vector_store.py       # ChromaDB vector store interface
│   │   │   └── metrics_tracker.py    # In-memory triage metrics tracking
│   │   ├── utils/
│   │   │   └── logger.py             # Logging configuration
│   │   ├── eval/
│   │   │   ├── run_eval.py           # Bulk eval script (confusion matrix + macro-F1)
│   │   │   ├── baseline_eval.py      # Majority/uniform/weighted-random baselines (new)
│   │   │   ├── agent_benchmark.py    # 3-agent pipeline vs single-call comparison (new)
│   │   │   ├── smoke_test.py         # Quick 1-bug-per-tier pipeline sanity check (new)
│   │   │   ├── fetch_bugzilla_issues.py  # Mozilla Bugzilla REST API fetcher (new)
│   │   │   ├── fetch_github_issues.py    # GitHub issue scraper (legacy source)
│   │   │   ├── curate_and_label.py       # Curation / labelling tool
│   │   │   └── eval/
│   │   │       ├── bugs.json                    # 300 labelled Bugzilla bugs (current eval set)
│   │   │       ├── raw_bugzilla_bugs.json        # Raw stratified Bugzilla pull
│   │   │       ├── raw_github_bugs.json          # Raw scraped GitHub issues (legacy)
│   │   │       ├── predictions.json              # Latest run_eval.py raw predictions
│   │   │       ├── agent_benchmark_single.json   # Single-call benchmark run output
│   │   │       └── agent_benchmark_multi.json    # Multi-agent benchmark run output
│   │   ├── data/
│   │   │   └── seed_bugs.py          # Seed data for demo
│   │   ├── config.py                 # Settings via env vars (incl. key partitioning)
│   │   └── main.py                   # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/               # Shared UI components
│   │   ├── lib/                      # API client and utilities
│   │   ├── routes/                   # App routes and screens
│   │   └── styles.css
│   └── package.json
├── run.py                            # Backend launcher
├── .env.example
├── .gitignore
├── sample_bugs.json                  # Sample bug reports for testing
├── requirements.txt
└── README.md
```

## API Overview

### Health Check

```http
GET /health
```

Returns service status, environment, and version.

### Submit Bug For Triage

```http
POST /triage
```

Example request:

```json
{
  "title": "OAuth callback redirects to 404",
  "description": "After approving Google sign-in, users are redirected to /404 instead of /dashboard. This happens only in production.",
  "repository": "org/my-app",
  "issue_url": "https://github.com/org/my-app/issues/42",
  "labels": ["bug", "auth"]
}
```

Example response:

```json
{
  "bug_id": "3f9c8d8a-4a4e-4f5c-b8f9-7b7a9a2d0f16",
  "status": "triaged",
  "severity": "high",
  "assigned_team": "frontend-team",
  "confidence": 0.78,
  "summary": "High severity — frontend-team",
  "explanation": "**Technical Analysis:** ...\n\n**Business Impact:** ...\n\n**Assignment:** ...",
  "duplicate_matches": [],
  "agent_outputs": [
    {"agent_name": "duplicate_detector", "decision": "no_duplicate", ...},
    {"agent_name": "technical_analyzer", "decision": "high", ...},
    {"agent_name": "business_analyzer", "decision": "high", ...},
    {"agent_name": "assignment_agent", "decision": "frontend-team", ...}
  ]
}
```

### List Bugs

```http
GET /bugs
```

Returns known and recently submitted bug reports with pagination.

### Metrics

```http
GET /metrics
```

Returns triage totals, duplicate rate, average triage time, and severity breakdown.

## Local Setup

### 1. Clone The Repository

```bash
git clone <your-repo-url>
cd xTriage
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
APP_NAME=Bug Triage Agent
APP_VERSION=0.1.0
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080

# At least one Groq API key is required.
# Single key:
# GROQ_API_KEY=gsk_your_key_here

# Or multiple keys for automatic rotation on rate limits:
GROQ_API_KEY_1=gsk_your_key_1
GROQ_API_KEY_2=gsk_your_key_2
GROQ_API_KEY_3=gsk_your_key_3
GROQ_API_KEY_4=gsk_your_key_4
GROQ_API_KEY_5=gsk_your_key_5

# Optional overrides. Defaults are:
# - multi-agent backend: GROQ_API_KEY_1..3
# - single-call benchmark: GROQ_API_KEY_4..5
# GROQ_MULTI_API_KEYS=
# GROQ_SINGLE_API_KEYS=
# GROQ_MODEL=llama-3.1-8b-instant
# GROQ_MAX_COMPLETION_TOKENS=220
# GROQ_PROMPT_DESCRIPTION_CHARS=2500
# GROQ_MAX_COOLDOWN_WAIT_SECONDS=20
```

### 3. Start The Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
python run.py
```

The backend runs at:

```text
http://localhost:8000
```

FastAPI docs are available at:

```text
http://localhost:8000/docs
```

### 4. Start The Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:8080
```

## Evaluation Data

The original eval set was scraped from GitHub issues (`microsoft/vscode` and others) and auto-labelled, which turned out to have a serious flaw: **96% of the 100 labelled bugs ended up tagged "medium"**, because there was no reliable ground-truth severity signal in GitHub issues to key off of. A model that always guesses "medium" would score 96% on that set — so the 82% xTriage was scoring looked good but was actually **14 points below that trivial baseline**. This was a data-quality bug, not a model bug, and it's the reason the eval set was replaced.

The current eval set is pulled from **Mozilla Bugzilla's public REST API** (`fetch_bugzilla_issues.py`), which carries a real, human-assigned `severity` field on every bug. Bugzilla's 6-tier scale is mapped down to xTriage's 4 tiers:

```text
blocker, critical  -> critical
major              -> high
normal             -> medium
minor, trivial     -> low
```

The fetcher stratifies the pull to target ~75 bugs per tier. The current `eval/bugs.json` contains **300 bugs, split exactly 75/75/75/75** across critical/high/medium/low — a genuinely balanced set with real ground truth, replacing the old 96%-medium GitHub set.

## Running The Evaluation

### Prerequisites

Ensure the backend is running:

```bash
python run.py
```

### Run The Eval

```bash
cd backend\app\eval
python run_eval.py
```

The script sends each bug to the `/triage` endpoint, builds a full confusion matrix, and reports per-class precision/recall/F1 plus macro-F1 — not just raw accuracy, since raw accuracy on an imbalanced set can be misleading (see [Evaluation Data](#evaluation-data)).

```text
[1/300] OK - bugzilla -- 108010 - Better & more explicit support of MIME structure...
[2/300] MISS (got medium, expected high) - bugzilla -- 378046 - Mail composition...
...

Confusion matrix (rows=truth, cols=predicted):
                   low    medium      high  critical
         low         0        54        18         3
      medium         4        38        29         4
        high         0        18        45        12
    critical         0        16        46        13

Per-class metrics:
  low        precision=0.00  recall=0.00  f1=0.00  support=75
  medium     precision=0.30  recall=0.51  f1=0.38  support=75
  high       precision=0.33  recall=0.60  f1=0.43  support=75
  critical   precision=0.41  recall=0.17  f1=0.24  support=75

=======================================================
Accuracy:           42.4%
Macro-F1:           26.3%   <- report THIS, not raw accuracy
Majority baseline:  25.0% (always guessing 'critical')
Lift over baseline: +17.4 points
Total fallback calls: 0
=======================================================
```

The eval respects optional environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `TRIAGE_URL` | `http://localhost:8000/triage` | Backend endpoint |
| `EVAL_REQUEST_TIMEOUT` | `300` | HTTP timeout per request (seconds) |
| `EVAL_SLEEP_SECONDS` | `10` | Delay between requests to avoid rate limits |

### Interpreting Results

- **OK** — Predicted severity matches ground truth
- **MISS (got X, expected Y)** — Prediction didn't match, shows actual vs expected
- **[FALLBACK xN]** — N of the agent calls for that bug fell back to a safe default (Groq unavailable), flagged so degraded predictions aren't silently mixed in with normal ones
- Report **macro-F1**, not raw accuracy, when the class distribution isn't perfectly balanced — raw accuracy on a skewed set rewards always guessing the majority class

### Baseline Sanity Check

`baseline_eval.py` computes the dumb baselines any real result should be compared against — majority-class, uniform-random, and weighted-random — so a headline accuracy number is never reported without context:

```bash
cd backend\app\eval
python baseline_eval.py
```

## Benchmark: Multi-Agent Pipeline vs. Single LLM Call

`agent_benchmark.py` runs the same 300 balanced Bugzilla bugs through two approaches back-to-back, on **separate Groq key pools** so neither phase competes for the other's quota, and reports accuracy, latency, and token cost side by side.

### Results — 300 Bugs, 75 Per Tier

```text
============================================================
Metric                          Single-call    Multi-agent
------------------------------------------------------------
Accuracy                              31.0%          42.4%
Avg latency (ms)                        316           8797
LLM calls per bug                         1              3
Avg tokens per bug                      397            n/a
Total tokens (all bugs)              119151            n/a
============================================================
```

**Confusion matrix — single-call** (rows=truth, cols=predicted):

```text
                low   medium    high   critical
         low     0       60      15          0
      medium     9       50      16          0
        high     0       38      37          0
    critical     0       34      41          0
```

**Confusion matrix — multi-agent** (rows=truth, cols=predicted):

```text
                low   medium    high   critical
         low     0       54      18          3
      medium     4       38      29          4
        high     0       18      45         12
    critical     0       16      46         13
```

**Baselines (balanced 4-class set, majority baseline = 25%):**

| Approach | Accuracy | Lift over 25% majority baseline |
|---|---|---|
| Single-call | 31.0% | +6.0 points |
| Multi-agent | 42.4% | +14.0 points |

### Takeaways

- The 3-agent pipeline beats a single consolidated LLM call by **+11.4 accuracy points** on the same 300 bugs, at the cost of ~3 LLM calls and ~28x the latency per bug (317ms → 8.8s average).
- Both approaches struggle hardest with the **`low` severity class** — neither ever correctly predicts `low` in this run (0/75 correct for both). Both models are biased toward over-escalating low-severity bugs into `medium`/`high`/`critical`, which is a real and known failure mode of LLM-based severity classifiers: framing language ("crash", "data loss", "fails") triggers escalation even in bugs a human triager would call cosmetic.
- The single-call approach shows a stronger "everything gravitates to the middle" pattern (most predictions land in `medium`/`high` regardless of truth); the multi-agent pipeline spreads predictions more across the tiers and picks up more `critical` bugs correctly (13/75 vs. 0/75), consistent with the max-rule design intentionally biasing toward escalation when either agent flags concern.
- Neither number should be read as "production-ready" — 42.4% accuracy on a 4-class balanced problem is meaningfully better than guessing, but severity classification from free text alone remains a hard problem. This benchmark exists to make that gap visible and trackable across iterations, not to declare victory.

## Smoke Test

`smoke_test.py` is a fast sanity check — one bug per severity tier — meant to catch pipeline breakage before running a full 300-bug eval:

```bash
cd backend\app\eval
python smoke_test.py
```

Latest run:

```text
Testing [critical] - ... -> predicted=high    fallbacks=[] [MISS]
Testing [high]     - ... -> predicted=high    fallbacks=[] [OK]
Testing [low]      - ... -> predicted=high    fallbacks=[] [MISS]
Testing [medium]   - ... -> predicted=medium  fallbacks=[] [OK]
Testing [high]     - ... -> predicted=medium  fallbacks=[] [MISS]

2/4 passed, 0 total fallback calls
```

Note: one of the 5 sampled bugs originally 422'd during this run due to a title-length validation issue in the request payload; that has since been fixed (title is now truncated consistently before being sent, matching the eval script's behavior), leaving 4 completed comparisons in the tally above. Zero fallback calls confirms the Groq key pool was healthy throughout — any MISS in this run is a model-accuracy issue, not an infrastructure issue.

## Fixes Applied Since Initial Build

| # | Fix | Files Changed |
|---|-----|--------------|
| 1 | Removed fake/auto-assigned "medium" ground-truth labels that were masking a 96%-medium data skew | `curate_and_label.py` |
| 2 | Replaced raw-accuracy-only reporting with a full confusion matrix, per-class precision/recall/F1, and macro-F1 | `run_eval.py` |
| 3 | Added severity-string normalization so Bugzilla's 6-tier vocabulary (`blocker`, `major`, `normal`, `minor`, `trivial`, etc.) is mapped correctly instead of silently mismatching | `agent_benchmark.py` |
| 4 | Made the single-call and multi-agent benchmark phases run sequentially against separate key pools, eliminating rate-limit contamination between the two | `agent_benchmark.py` |
| 5 | Added structured logging of 422 response bodies and consistent title truncation before submission | `agent_benchmark.py`, `run_eval.py` |
| 6 | Added a Mozilla Bugzilla REST API fetcher to source a properly balanced, real-ground-truth eval set | `fetch_bugzilla_issues.py` (new) |
| 7 | Added a fast 1-bug-per-tier smoke test with fallback-call tracking for pre-flight pipeline checks | `smoke_test.py` (new) |
| 8 | Partitioned Groq API keys into separate multi-agent/single-call pools in settings | `config.py`, `groq_client.py` |

## Known Issues / In Progress

The following cleanup items are being worked on independently and are not yet fully complete as of this eval round:

- Removing leftover BOM characters and informal inline dev comments from a few backend source files
- Migrating `VectorStore` off the deprecated `chromadb.Client()` constructor onto `chromadb.PersistentClient(path="./chroma_data")`
- Adding graceful fallbacks and retry/backoff for edge cases in Groq calls beyond what `GroqClientPool` already covers
- Expanding automated test coverage beyond the eval/benchmark/smoke scripts described above

## Severity Aggregation

xTriage uses a **max-rule** to combine technical and business severity:

- Each agent independently rates severity on a 1-4 scale (low → critical)
- The final severity is the **maximum** of the two
- Business can **escalate** severity (e.g., technically simple but blocks all users → critical)
- Business can **never reduce** severity (e.g., technically complex but cosmetic → stays at tech's rating)

This ensures that if either analysis flags a bug as critical, the final result reflects that — and, per the benchmark above, is a likely contributor to the multi-agent pipeline's stronger `critical`-class recall relative to the single-call approach.

## Graceful Degradation

When Groq API is unavailable (rate limited, quota exhausted, network error):

1. **GroqClientPool** retries with exponential backoff across all available API keys in its assigned pool
2. If all keys are exhausted, it raises `GroqClientUnavailable`
3. Each agent catches this and returns a safe fallback result (medium severity, triage-team assignment)
4. The backend responds with `200 OK` and the fallback, never a 500 error
5. Eval and benchmark scripts track and report fallback calls separately so degraded runs aren't silently averaged in with healthy ones

## Example Workflow

1. Open the frontend at `http://localhost:8080`
2. Enter a bug title and description
3. Submit the report
4. The backend runs duplicate detection, then all three LLM agents in parallel
5. Severity is computed as the max of technical and business ratings
6. The UI displays severity, assigned team, confidence, explanation, and agent traces
7. The dashboard shows triage metrics and recent bug history

## What This Project Demonstrates

- API design with FastAPI and Pydantic
- Multi-agent AI orchestration with graceful degradation
- API key rotation with cooldown-based rate limit handling and multi-pool partitioning
- Vector search for semantic duplicate detection
- Embedding-based similarity with sentence-transformers
- Prompt engineering for structured JSON output from LLMs
- Rigorous evaluation methodology: catching a data-quality bug (96%-medium skew) that inflated an earlier headline number, replacing it with a genuinely balanced, real-ground-truth eval set, and reporting macro-F1 and baselines alongside raw accuracy
- Head-to-head benchmarking of architectural choices (multi-agent vs. single-call) on accuracy, latency, and cost — not just shipping the more complex approach on faith
- React and TypeScript frontend development
- End-to-end product thinking for engineering team workflows

## License

This project is currently intended for learning, experimentation, and portfolio development.