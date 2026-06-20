from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.app.services.metrics_tracker import metrics


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
	data = metrics.snapshot()
	return MetricsSnapshot(**data)
