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

xTriage explores how an AI system can assist that workflow by combining deterministic API design, vector similarity search, and specialized analysis agents.

## Features

- **Bug report intake** — Submit bug reports with title, description, and optional metadata
- **Technical severity analysis** — LLM-powered analysis of bug complexity, affected components, and severity
- **Business impact analysis** — LLM-powered analysis of user impact, revenue risk, and priority
- **Duplicate detection** — Semantic similarity search using sentence-transformer embeddings and ChromaDB
- **Team assignment** — LLM-powered recommendation of the engineering team that should handle the bug
- **Max-rule severity aggregation** — Business analysis can escalate severity, never reduce it (max of tech + business)
- **Groq API key rotation** — Automatic rotation across multiple API keys with cooldown on rate limits, exponential backoff, and smart retry-after header parsing
- **Explainable triage** — Full agent trace with rationale, confidence scores, and signals
- **Evaluation pipeline** — Bulk eval script that runs 100 labelled bugs and reports severity accuracy
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
│   │   │   ├── run_eval.py           # Bulk eval script (100 labelled bugs)
│   │   │   ├── fetch_github_issues.py # GitHub issue scraper for eval data
│   │   │   ├── curate_and_label.py   # Manual labelling tool
│   │   │   └── eval/
│   │   │       ├── bugs.json         # 100 labelled bugs for eval
│   │   │       └── raw_github_bugs.json # Raw scraped issues
│   │   ├── data/
│   │   │   └── seed_bugs.py          # Seed data for demo
│   │   ├── config.py                 # Settings via env vars
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

# Optional overrides:
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

## Running The Evaluation

The project includes 100 manually labelled bug reports for evaluating severity prediction accuracy.

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

The script sends each bug to the `/triage` endpoint, compares the predicted severity against ground truth, and reports overall accuracy.

```text
[1/100] OK - microsoft -- vscode -- 321387 - Copy/Paste files broken
[2/100] OK - microsoft -- vscode -- 322826 - Visual Studio Code 1.126: ...
[3/100] MISS (got medium, expected high) - microsoft -- vscode -- 322527 - ...

...

==================================================
Severity Accuracy: 82/100 = 82.0%
Errors: 0
==================================================
```

The eval respects optional environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `TRIAGE_URL` | `http://localhost:8000/triage` | Backend endpoint |
| `EVAL_REQUEST_TIMEOUT` | `300` | HTTP timeout per request (seconds) |
| `EVAL_SLEEP_SECONDS` | `5` | Delay between requests to avoid rate limits |

### Interpreting Results

- **OK** — Predicted severity matches ground truth
- **MISS (got X, expected Y)** — Prediction didn't match, shows actual vs expected
- **ERROR** — Backend returned non-200 or request failed

## Severity Aggregation

xTriage uses a **max-rule** to combine technical and business severity:

- Each agent independently rates severity on a 1-4 scale (low → critical)
- The final severity is the **maximum** of the two
- Business can **escalate** severity (e.g., technically simple but blocks all users → critical)
- Business can **never reduce** severity (e.g., technically complex but cosmetic → stays at tech's rating)

This ensures that if either analysis flags a bug as critical, the final result reflects that.

## Graceful Degradation

When Groq API is unavailable (rate limited, quota exhausted, network error):

1. **GroqClientPool** retries with exponential backoff across all available API keys
2. If all keys are exhausted, it raises `GroqClientUnavailable`
3. Each agent catches this and returns a safe fallback result (medium severity, triage-team assignment)
4. The backend responds with `200 OK` and the fallback, never a 500 error

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
- API key rotation with cooldown-based rate limit handling
- Vector search for semantic duplicate detection
- Embedding-based similarity with sentence-transformers
- Prompt engineering for structured JSON output from LLMs
- Evaluation pipeline for measuring and iterating on accuracy
- React and TypeScript frontend development
- End-to-end product thinking for engineering team workflows

## License

This project is currently intended for learning, experimentation, and portfolio development.