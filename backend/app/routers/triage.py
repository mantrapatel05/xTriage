from time import perf_counter

from fastapi import APIRouter, status

from backend.app.models.bug import BugReport
from backend.app.models.triage_result import TriageResult
from backend.app.agents.triage_lead import TriageLead
from backend.app.routers.bugs import SAMPLE_BUGS
from backend.app.services.metrics_tracker import metrics

router = APIRouter(tags=["triage"])
triage_lead = TriageLead()


@router.post("/triage", response_model=TriageResult, status_code=status.HTTP_200_OK)
async def triage_bug(bug: BugReport) -> TriageResult:
    started_at = perf_counter()
    result = triage_lead.orchestrate(bug)
    duration_seconds = perf_counter() - started_at

    metrics.record_triage(result, duration_seconds)
    SAMPLE_BUGS.insert(
        0,
        bug.model_copy(
            update={
                "bug_id": result.bug_id,
                "severity_hint": result.severity,
                "status": result.status,
            }
        ),
    )

    return result
