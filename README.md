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

- Bug report intake with title and description
- Technical severity analysis
- Business impact analysis
- Duplicate detection using embeddings and vector search
- Team assignment recommendation
- Explainable triage result with agent traces
- Metrics endpoint for triage counts and severity distribution
- React dashboard for submission, history, and telemetry
- Typed backend models with Pydantic
- FastAPI OpenAPI documentation

## Tech Stack

### Backend

- Python
- FastAPI
- Pydantic
- Groq API for LLM-powered agents
- ChromaDB for vector storage
- sentence-transformers for text embeddings
- Uvicorn

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
        +--> Technical analyzer agent
        |
        +--> Business impact agent
        |
        +--> Assignment agent
        |
        v
Triage result
        |
        +--> Severity
        +--> Assigned team
        +--> Confidence
        +--> Explanation
        +--> Agent trace
        +--> Duplicate matches
```

## Repository Structure

```text
xTriage/
  backend/
    app/
      agents/          # Technical, business, duplicate, and assignment agents
      models/          # Pydantic request and response models
      routers/         # FastAPI route modules
      services/        # Embeddings, vector store, and metrics services
      utils/           # Logging utilities
      main.py          # FastAPI application entry point
    requirements.txt

  frontend/
    src/
      components/      # Shared UI components
      lib/             # API client and utilities
      routes/          # App routes and screens
      styles.css
    package.json

  run.py               # Backend launcher
  .env.example
  README.md
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
  "description": "After approving Google sign-in, users are redirected to /404 instead of /dashboard. This happens only in production."
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
  "summary": "High severity - frontend-team",
  "explanation": "Technical, business, and assignment analysis...",
  "duplicate_matches": [],
  "agent_outputs": []
}
```

### List Bugs

```http
GET /bugs
```

Returns known and recently submitted bug reports.

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
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Start The Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
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

## Example Workflow

1. Open the frontend.
2. Enter a bug title and description.
3. Submit the report.
4. The backend runs duplicate detection and agent analysis.
5. The UI displays severity, assigned team, summary, explanation, and agent trace.
6. The dashboard shows triage metrics and recent bug history.

## What This Project Demonstrates

- API design with FastAPI
- Typed backend data modeling with Pydantic
- AI agent orchestration
- Vector search for duplicate detection
- Embedding-based semantic similarity
- React and TypeScript frontend development
- End-to-end product thinking
- Practical AI workflow design for engineering teams

## License

This project is currently intended for learning, experimentation, and portfolio development.
