from fastapi import APIRouter, status

from backend.app.models.bug import BugReport, SeverityLevel, TriageStatus
from backend.app.models.triage_result import AgentOutput, TriageResult


router = APIRouter(tags=["triage"])


@router.post("/triage", response_model=TriageResult, status_code=status.HTTP_200_OK)
async def triage_bug(bug: BugReport) -> TriageResult:
	severity = bug.severity_hint or SeverityLevel.medium

	agent_outputs = [
		AgentOutput(
			agent_name="technical_analyzer",
			decision="review",
			rationale="Scaffold response; technical analysis is not wired yet.",
			confidence=0.3,
			signals=[bug.title, bug.description[:120]],
		),
		AgentOutput(
			agent_name="business_analyzer",
			decision="needs_review",
			rationale="Business impact scoring will be added in a later commit.",
			confidence=0.3,
			signals=[bug.reporter or "unknown reporter"],
		),
		AgentOutput(
			agent_name="assignment_agent",
			decision="triage_team",
			rationale="Assignment logic is stubbed for the initial scaffold.",
			confidence=0.4,
			signals=[bug.repository or "unknown repository"],
		),
	]

	return TriageResult(
		bug_id=bug.bug_id,
		status=TriageStatus.triaged,
		severity=severity,
		assigned_team="triage-team",
		confidence=0.42,
		summary=f"Scaffold triage for: {bug.title}",
		explanation="This response proves the API contract before the real agents are implemented.",
		duplicate_matches=[],
		agent_outputs=agent_outputs,
	)
