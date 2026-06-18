from fastapi import APIRouter, status

from backend.app.models.bug import BugReport
from backend.app.models.triage_result import TriageResult
from backend.app.agents.triage_lead import TriageLead

router = APIRouter(tags=["triage"])
triage_lead = TriageLead()


@router.post("/triage", response_model=TriageResult, status_code=status.HTTP_200_OK)
async def triage_bug(bug: BugReport) -> TriageResult:
    return triage_lead.orchestrate(bug)
