from groq import Groq
from backend.app.config import get_settings
from backend.app.models.bug import BugReport
from backend.app.models.triage_result import AgentOutput


ASSIGNMENT_PROMPT = """You are a Triage Assignment Agent. Based on the bug details and analysis context, recommend who should fix this bug. Respond with ONLY valid JSON.

Bug Title: {title}
Description: {description}
Severity Hint: {severity_hint}
Repository: {repository}
Labels: {labels}
Technical Analysis: {tech_analysis}
Business Impact: {business_analysis}

Available teams:
- "frontend-team" (UI, editor, extensions)
- "backend-team" (APIs, services, database)
- "infrastructure-team" (devops, build, CI/CD)
- "core-team" (language server, debugging, core features)
- "security-team" (vulnerabilities, auth, permissions)
- "docs-team" (documentation, error messages)
- "triage-team" (unclear, needs investigation)

Output JSON format:
{{
  "assigned_team": "team-name",
  "assignee": "recommended-person or null",
  "rationale": "2-3 sentence explanation",
  "signals": ["key factors in this decision"]
}}
"""


class AssignmentAgent:
    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"

    def assign(self, bug: BugReport, tech_analysis: str = "", business_analysis: str = "") -> AgentOutput:
        prompt = ASSIGNMENT_PROMPT.format(
            title=bug.title,
            description=bug.description,
            severity_hint=bug.severity_hint.value if bug.severity_hint else "not specified",
            repository=bug.repository or "unknown",
            labels=", ".join(bug.labels) if bug.labels else "none",
            tech_analysis=tech_analysis or "pending",
            business_analysis=business_analysis or "pending",
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        result = self._parse_response(response.choices[0].message.content)

        return AgentOutput(
            agent_name="assignment_agent",
            decision=result.get("assigned_team", "triage-team"),
            rationale=result.get("rationale", "Assignment recommendation completed"),
            confidence=self._calculate_confidence(result),
            signals=result.get("signals", [bug.repository or "unknown"]),
        )

    def _parse_response(self, text: str) -> dict:
        import json, re
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"assigned_team": "triage-team", "rationale": "Failed to parse AI response", "signals": []}

    def _calculate_confidence(self, result: dict) -> float:
        team = result.get("assigned_team", "")
        if team and team != "triage-team":
            return 0.75
        return 0.4