# main thing to tackle here is to analyze the bug technically deeply
from backend.app.models.bug import BugReport, SeverityLevel
from backend.app.models.triage_result import AgentOutput
from backend.app.config import get_settings
from backend.app.services.groq_client import GroqClientUnavailable, get_groq_client

TECH_PROMPT = """
You are a Technical Triage Analyst. Analyze this bug report and respond with ONLY valid JSON (no markdown, no backticks).

Bug Title: {title}
Description: {description}
Steps to Reproduce: {steps}
Expected Behavior: {expected}
Actual Behavior: {actual}
Labels: {labels}

Output JSON format:
{{
  "severity": "low" | "medium" | "high" | "critical",
  "affected_components": ["component1", "component2"],
  "fix_complexity": "trivial" | "moderate" | "complex" | "unknown",
  "rationale": "2-3 sentence technical explanation",
  "signals": ["key technical indicators found"]
}}
"""


class TechnicalAnalyzer:
    def __init__(self):
        self.client = get_groq_client()
        settings = get_settings()
        self.model = settings.groq_model
        self.max_tokens = settings.groq_max_completion_tokens
        self.max_desc_chars = settings.groq_prompt_description_chars

    # code area where it has been affected
    def analyze(self, bug: BugReport) -> AgentOutput:
        desc = bug.description[:self.max_desc_chars] if bug.description else ""
        prompt = TECH_PROMPT.format(
            title=bug.title,
            description=desc,
            steps="; ".join(bug.steps_to_reproduce) if bug.steps_to_reproduce else "Not provided",
            expected=bug.expected_behavior or "Not specified",
            actual=bug.actual_behavior or "Not specified",
            labels=", ".join(bug.labels) if bug.labels else "None",
        )

        try:
            response = self.client.chat_completions_create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=self.max_tokens,
            )
            result = self._parse_response(response.choices[0].message.content)
        except GroqClientUnavailable as e:
            print(f"  [TechnicalAnalyzer] Groq unavailable: {e}")
            result = {"severity": "medium", "rationale": "Technical analysis unavailable (Groq API down)", "signals": []}
        except Exception as e:
            print(f"  [TechnicalAnalyzer] Analysis failed: {e}")
            result = {"severity": "medium", "rationale": "Technical analysis failed; using safe default", "signals": []}

        return AgentOutput(
            agent_name="technical_analyzer",
            decision=result.get("severity", "medium"),
            rationale=result.get("rationale", "Technical analysis completed"),
            confidence=self._calculate_confidence(result),
            signals=result.get("signals", [bug.title]),
        )

    # i have to write the func to check the severity of the bug
    def _parse_response(self, text: str) -> dict:
        import json, re
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"severity": "medium", "rationale": "Failed to parse AI response", "signals": []}

    def _calculate_confidence(self, result: dict) -> float:
        complexity_map = {"trivial": 0.9, "moderate": 0.7, "complex": 0.5, "unknown": 0.3}
        base = complexity_map.get(result.get("fix_complexity", "unknown"), 0.3)
        signal_bonus = min(len(result.get("signals", [])) * 0.05, 0.2)
        return round(min(base + signal_bonus, 1.0), 2)
