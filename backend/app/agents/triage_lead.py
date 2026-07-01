import uuid
from datetime import datetime, timezone

from backend.app.models.bug import BugReport
from backend.app.models.triage_result import TriageResult
from backend.app.agents.technical_analyzer import TechnicalAnalyzer
from backend.app.agents.business_analyzer import BusinessAnalyzer
from backend.app.agents.duplicate_detector import DuplicateDetector
from backend.app.agents.assignment_agent import AssignmentAgent


class TriageLead:
    def __init__(self):
        self.technical = TechnicalAnalyzer()
        self.business = BusinessAnalyzer()
        self.duplicates = DuplicateDetector()
        self.assignment = AssignmentAgent()

    def orchestrate(self, bug: BugReport) -> TriageResult:
        bug_id = bug.bug_id or str(uuid.uuid4())

        # Step 1: Find duplicates (fast, doesn't need LLM)
        duplicate_matches, duplicate_output = self.duplicates.search(bug)

        # If exact duplicate found, short-circuit
        if duplicate_output.decision == "duplicate_found":
            return TriageResult(
                bug_id=bug_id,
                status="duplicate",
                severity=bug.severity_hint or "medium",
                assigned_team="triage-team",
                confidence=duplicate_output.confidence,
                summary=f"Duplicate of: {duplicate_matches[0].title}",
                explanation=duplicate_output.rationale,
                duplicate_matches=duplicate_matches,
                agent_outputs=[duplicate_output],
            )

        # Step 2: Run all LLM agents
        tech_output = self.technical.analyze(bug)
        business_output = self.business.analyze(bug)
        assignment_output = self.assignment.assign(
            bug,
            tech_analysis=tech_output.rationale,
            business_analysis=business_output.rationale,
        )

        # Step 3: Synthesize final severity (max rule — either can escalate, never reduce)
        rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        reverse_rank = {1: "low", 2: "medium", 3: "high", 4: "critical"}
        tech_rank = rank.get(tech_output.decision, 2)
        business_rank = rank.get(business_output.decision, 2)
        final_rank = max(tech_rank, business_rank)
        final_severity = reverse_rank[final_rank]

        # Step 4: Calculate overall confidence
        confidences = [tech_output.confidence, business_output.confidence, assignment_output.confidence]
        if duplicate_output.confidence > 0.5:
            confidences.append(duplicate_output.confidence)
        overall_confidence = round(sum(confidences) / len(confidences), 2)

        # Step 5: Build explanation
        explanation_parts = [
            f"**Technical Analysis:** {tech_output.rationale}",
            f"**Business Impact:** {business_output.rationale}",
            f"**Assignment:** {assignment_output.rationale}",
        ]
        if duplicate_matches:
            explanation_parts.append(f"**Related Bugs Found:** {len(duplicate_matches)} similar bugs in history")
        explanation = "\n\n".join(explanation_parts)

        return TriageResult(
            bug_id=bug_id,
            status="triaged",
            severity=final_severity,
            assigned_team=assignment_output.decision,
            confidence=overall_confidence,
            summary=f"{final_severity.capitalize()} severity — {assignment_output.decision}",
            explanation=explanation,
            duplicate_matches=duplicate_matches,
            agent_outputs=[duplicate_output, tech_output, business_output, assignment_output],
        )