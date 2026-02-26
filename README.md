# xTriage

`xTriage` is a base-level Bug Triage Agent built with Flask and simple rule-based logic.

This is the first version of my vision: an intelligent triage system that can read bug reports, summarize them, assign priority, and route them to the right team automatically.

## Current Status (MVP)

Right now, the project supports:
- Bug summary generation
- Priority classification (`High`, `Medium`, `Low`, `Very low`)
- Team routing (`Core`, `Frontend`, `Backend`, `Documentation`, `Database`, `Uncategorized`)
- JSON API endpoint for triaging issues

The current logic is keyword-based and intentionally simple as a foundation.

## Project Structure

```text
xTriage/
  app.py
  requirements.txt
  sample_bugs.json
  triage/
    summarizer.py
    priority.py
    router.py
```

## API Routes

### `GET /`
Health route.

Response:
```text
Bug Triage System is running.
```

### `POST /triage`
Accepts a bug JSON payload and returns triage results.

Example request body:
```json
{
  "title": "Login fails when JWT token expires",
  "description": "Users receive a 500 error when token is expired during authentication.",
  "comments": [
    "Issue started after last backend deployment.",
    "JWT validation logic might be broken."
  ]
}
```

Example response shape:
```json
{
  "summary": "...",
  "priority": "High",
  "assigned_team": "Core",
  "confidence": 0.9,
  "reasons": ["Contains high-priority keywords"]
}
```

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Server runs on:
- `http://127.0.0.1:5000`
- `http://localhost:5000`

## My Vision

This is just the base layer. The long-term goal is to evolve `xTriage` into a real AI triage agent that can:
- Understand issue context beyond keywords
- Learn from triage history
- Integrate with tools like GitHub/Jira
- Predict urgency and owner with better confidence
- Provide explainable triage decisions for teams

This repo is the starting point for that system.