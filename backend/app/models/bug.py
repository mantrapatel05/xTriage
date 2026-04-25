from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SeverityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TriageStatus(str, Enum):
    new = "new"
    triaged = "triaged"
    duplicate = "duplicate"
    needs_info = "needs_info"
    assigned = "assigned"


class BugReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bug_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    steps_to_reproduce: list[str] = Field(default_factory=list)
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    severity_hint: SeverityLevel | None = None
    status: TriageStatus = TriageStatus.new
    reporter: str | None = None
    repository: str | None = None
    issue_url: str | None = None
    labels: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))