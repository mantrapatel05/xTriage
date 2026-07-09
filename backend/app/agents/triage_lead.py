from __future__ import annotations

import uuid
from typing import Optional

from backend.app.agents.assignment_agent import AssignmentAgent
from backend.app.agents.business_analyzer import BusinessAnalyzer
from backend.app.agents.duplicate_detector import DuplicateDetector
from backend.app.agents.technical_analyzer import TechnicalAnalyzer
from backend.app.models.bug import BugReport
from backend.app.models.triage_result import TriageResult
from backend.app.services.vector_store import VectorStore


class TriageLead:
    def __init__(
        self,
        vector_store: VectorStore | None = None,
        technical: TechnicalAnalyzer | None = None,
        business: BusinessAnalyzer | None = None,
        duplicates: DuplicateDetector | None = None,
        assignment: AssignmentAgent | None = None,
    ) -> None:
        self.store = vector_store or VectorStore()
        self.technical = technical or TechnicalAnalyzer()
        self.business = business or BusinessAnalyzer()
        self.duplicates = duplicates or DuplicateDetector()
        self.assignment = assignment or AssignmentAgent()

    # ------------------------------------------------------------------
    # Main orchestration
    # ------------------------------------------------------------------
    def orchestrate(self, bug: BugReport) -> TriageResult:
        bug_id = bug.bug_id or str(uuid.uuid4())

        # 1. Duplicate detection (fast, no LLM)
        duplicate_matches, duplicate_output = self.duplicates.search(bug)
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

        # 2. Retrieve historical context (RAG)
        historical_matches = self.store.retrieve_similar_with_metadata(
            query=f"{bug.title}\n{bug.description}",
            n_results=3,
            threshold=0.5,
        )
        context_str = self._format_context_for_prompt(historical_matches)

        # 3. Run all LLM agents with the retrieved context
        tech_output = self.technical.analyze(bug, context=context_str)
        business_output = self.business.analyze(bug, context=context_str)
        assignment_output = self.assignment.analyze(
            bug,
            tech_analysis=tech_output.rationale,
            business_analysis=business_output.rationale,
            context=context_str,
        )

        # 4. Max-rule severity aggregation (business can escalate, never reduce)
        rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        reverse_rank = {1: "low", 2: "medium", 3: "high", 4: "critical"}
        tech_rank = rank.get(tech_output.decision, 2)
        business_rank = rank.get(business_output.decision, 2)
        final_severity = reverse_rank[max(tech_rank, business_rank)]

        # 5. Overall confidence
        confidences = [
            tech_output.confidence,
            business_output.confidence,
            assignment_output.confidence,
        ]
        if duplicate_output.confidence > 0.5:
            confidences.append(duplicate_output.confidence)
        overall_confidence = round(sum(confidences) / len(confidences), 2)

        # 6. Build explanation
        explanation_parts = [
            f"**Technical Analysis:** {tech_output.rationale}",
            f"**Business Impact:** {business_output.rationale}",
            f"**Assignment:** {assignment_output.rationale}",
        ]
        if duplicate_matches:
            explanation_parts.append(
                f"**Related Bugs Found:** {len(duplicate_matches)} similar bugs in history"
            )
        if historical_matches:
            explanation_parts.append(
                f"**Historical Context Used:** {len(historical_matches)} similar bugs retrieved for prompting"
            )
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
            agent_outputs=[
                duplicate_output,
                tech_output,
                business_output,
                assignment_output,
            ],
        )

    # ------------------------------------------------------------------
    # Helper: format retrieved bugs as a prompt block
    # ------------------------------------------------------------------
    def _format_context_for_prompt(self, retrieved_bugs: list[dict]) -> str:
        if not retrieved_bugs:
            return ""
        lines = ["Historical Context (similar past bugs):"]
        for i, item in enumerate(retrieved_bugs, 1):
            meta = item.get("metadata", {})
            lines.append(
                f"{i}. bug_id={meta.get('bug_id', '?')}  "
                f"similarity={item['similarity']:.2f}  "
                f"severity={meta.get('severity', '?')}  "
                f"resolution={meta.get('resolution', '?')}  "
                f"component={meta.get('component', '?')}  "
                f"team={meta.get('team', '?')}"
            )
            lines.append(f"   title: {meta.get('title', 'unknown')}")
            lines.append(f"   summary: {item.get('document', '')[:300]}")
        return "\n".join(lines)