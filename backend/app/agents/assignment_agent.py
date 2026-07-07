from backend.app.models.bug import BugReport
from backend.app.models.triage_result import AgentOutput
from backend.app.config import get_settings
from backend.app.services.groq_client import GroqClientUnavailable, get_groq_client


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
        self.client = get_groq_client()
        settings = get_settings()
        self.model = settings.groq_model
        self.max_tokens = settings.groq_max_completion_tokens
        self.max_desc_chars = settings.groq_prompt_description_chars

    def assign(self, bug: BugReport, tech_analysis: str = "", business_analysis: str = "") -> AgentOutput:
        desc = bug.description[:self.max_desc_chars] if bug.description else ""
        prompt = ASSIGNMENT_PROMPT.format(
            title=bug.title,
            description=desc,
            severity_hint=bug.severity_hint.value if bug.severity_hint else "not specified",
            repository=bug.repository or "unknown",
            labels=", ".join(bug.labels) if bug.labels else "none",
            tech_analysis=tech_analysis or "pending",
            business_analysis=business_analysis or "pending",
        )

        used_fallback = False
        try:
            response = self.client.chat_completions_create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=self.max_tokens,
            )
            result = self._parse_response(response.choices[0].message.content)
            if result.get("_parse_failed"):
                used_fallback = True
        except GroqClientUnavailable as e:
            print(f"  [AssignmentAgent] Groq unavailable: {e}")
            used_fallback = True
            result = {"assigned_team": "triage-team", "rationale": "Assignment unavailable (Groq API down)", "signals": []}
        except Exception as e:
            print(f"  [AssignmentAgent] Assignment failed: {e}")
            used_fallback = True
            result = {"assigned_team": "triage-team", "rationale": "Assignment failed; using triage-team fallback", "signals": []}

        return AgentOutput(
            agent_name="assignment_agent",
            decision=result.get("assigned_team", "triage-team"),
            rationale=result.get("rationale", "Assignment recommendation completed"),
            confidence=self._calculate_confidence(result),
            signals=result.get("signals", [bug.repository or "unknown"]),
            used_fallback=used_fallback,
        )

    def _parse_response(self, text: str) -> dict:
        import json, re
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "assigned_team": "triage-team",
                "rationale": "Failed to parse AI response",
                "signals": [],
                "_parse_failed": True,
            }

    def _calculate_confidence(self, result: dict) -> float:
        team = result.get("assigned_team", "")
        if team and team != "triage-team":
            return 0.75
        return 0.4
