# tackling here is to tackle is a bug from a business(money) perspective too
from backend.app.models.bug import BugReport
from backend.app.models.triage_result import AgentOutput
from backend.app.config import get_settings
from backend.app.services.groq_client import GroqClientUnavailable, get_groq_client

BUSINESS_PROMPT = """You are a Business Impact Analyst. Analyze this bug report and respond with ONLY valid JSON (no markdown, no backticks).

Priority definitions (pick exactly one):
- p0 / critical: users blocked from core workflows, revenue at risk, or data loss
- p1 / high: major feature broken for many users; significant support load expected
- p2 / medium: partial degradation; workaround available; moderate user annoyance
- p3 / low: cosmetic, edge-case, or internal-only; minimal user or revenue impact

Calibration examples:
- "Payment processing down for all customers" -> p0
- "Search returns no results for 30% of users" -> p1
- "Dashboard chart renders incorrectly but data is correct in export" -> p2
- "Wrong icon color in settings panel" -> p3

Bug Title: {title}
Description: {description}
Severity Hint: {severity_hint}
Reporter: {reporter}

Output JSON format:
{{
  "reasoning": "one sentence explaining why this priority fits",
  "priority": "p0" | "p1" | "p2" | "p3",
  "user_impact": "none" | "few" | "many" | "all",
  "business_rationale": "2-3 sentence business impact explanation",
  "recommended_sla_hours": 1 | 4 | 24 | 72 | 168,
  "signals": ["key business indicators"]
}}
"""


class BusinessAnalyzer:
    def __init__(self):
        self.client = get_groq_client()
        settings = get_settings()
        self.model = settings.groq_model
        self.max_tokens = settings.groq_max_completion_tokens
        self.max_desc_chars = settings.groq_prompt_description_chars

    def analyze(self, bug: BugReport) -> AgentOutput:
        desc = bug.description[:self.max_desc_chars] if bug.description else ""
        prompt = BUSINESS_PROMPT.format(
            title=bug.title,
            description=desc,
            severity_hint=bug.severity_hint.value if bug.severity_hint else "not specified",
            reporter=bug.reporter or "unknown",
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
            print(f"  [BusinessAnalyzer] Groq unavailable: {e}")
            used_fallback = True
            result = {"priority": "p2", "business_rationale": "Business analysis unavailable (Groq API down)", "signals": []}
        except Exception as e:
            print(f"  [BusinessAnalyzer] Analysis failed: {e}")
            used_fallback = True
            result = {"priority": "p2", "business_rationale": "Business analysis failed; using safe default", "signals": []}

        priority_map = {"p0": "critical", "p1": "high", "p2": "medium", "p3": "low"}
        return AgentOutput(
            agent_name="business_analyzer",
            decision=priority_map.get(result.get("priority", "p2"), "medium"),
            rationale=result.get("business_rationale", "Business analysis completed"),
            confidence=self._calculate_confidence(result),
            signals=result.get("signals", []),
            used_fallback=used_fallback,
        )

    def _parse_response(self, text: str) -> dict:
        import json, re
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "priority": "p2",
                "business_rationale": "Failed to parse AI response",
                "signals": [],
                "_parse_failed": True,
            }

    def _calculate_confidence(self, result: dict) -> float:
        priority_conf = {"p0": 0.9, "p1": 0.8, "p2": 0.6, "p3": 0.5}
        base = priority_conf.get(result.get("priority", "p2"), 0.5)
        signal_bonus = min(len(result.get("signals", [])) * 0.05, 0.2)
        return round(min(base + signal_bonus, 1.0), 2)
