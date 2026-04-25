from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(tags=["metrics"])


class MetricsSnapshot(BaseModel):
	total_bugs: int = Field(ge=0)
	triaged_bugs: int = Field(ge=0)
	duplicate_rate: float = Field(ge=0, le=1)
	average_triage_seconds: float = Field(ge=0)
	severity_breakdown: dict[str, int]
	last_updated: datetime


@router.get("/metrics", response_model=MetricsSnapshot)
async def get_metrics() -> MetricsSnapshot:
	return MetricsSnapshot(
		total_bugs=2,
		triaged_bugs=1,
		duplicate_rate=0.0,
		average_triage_seconds=2.4,
		severity_breakdown={"low": 0, "medium": 1, "high": 1, "critical": 0},
		last_updated=datetime.now(timezone.utc),
	)
