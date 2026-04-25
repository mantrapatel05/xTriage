from fastapi import APIRouter, HTTPException, Query

from backend.app.models.bug import BugReport, SeverityLevel, TriageStatus


router = APIRouter(tags=["bugs"])


SAMPLE_BUGS = [
	BugReport(
		bug_id="bug-001",
		title="Crash on save in the editor",
		description="The application crashes when the user saves a file after editing.",
		steps_to_reproduce=["Open a file", "Edit the file", "Press Save"],
		expected_behavior="The file should save without crashing.",
		actual_behavior="The app crashes immediately after save.",
		severity_hint=SeverityLevel.high,
		status=TriageStatus.triaged,
		reporter="sample-user",
		repository="microsoft/vscode",
		labels=["crash", "save"],
	),
	BugReport(
		bug_id="bug-002",
		title="Search results are empty for valid query",
		description="Search returns no results even when matching files exist.",
		steps_to_reproduce=["Open search", "Search for a known filename"],
		expected_behavior="Relevant files should appear.",
		actual_behavior="The results panel is empty.",
		severity_hint=SeverityLevel.medium,
		status=TriageStatus.new,
		reporter="sample-user",
		repository="microsoft/vscode",
		labels=["search", "regression"],
	),
]


@router.get("/bugs", response_model=list[BugReport])
async def list_bugs(limit: int = Query(default=20, ge=1, le=100)) -> list[BugReport]:
	return SAMPLE_BUGS[:limit]


@router.get("/bugs/{bug_id}", response_model=BugReport)
async def get_bug(bug_id: str) -> BugReport:
	for bug in SAMPLE_BUGS:
		if bug.bug_id == bug_id:
			return bug
	raise HTTPException(status_code=404, detail="Bug not found")
