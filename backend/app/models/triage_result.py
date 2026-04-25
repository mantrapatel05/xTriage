from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from .bug import SeverityLevel, TriageStatus


class AgentOutput(BaseModel):
    agent_name: str
    decision: str
    rationale: str
    confidence: float = Field(ge=0, le=1)
    signals: list[str] = Field(default_factory=list)


class DuplicateMatch(BaseModel):
    bug_id: str | None = None
    title: str
    similarity: float = Field(ge=0, le=1)
    rationale: str | None = None
    issue_url: str | None = None


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bug_id: str | None = None
    status: TriageStatus
    severity: SeverityLevel
    assigned_team: str
    confidence: float = Field(ge=0, le=1)
    summary: str
    explanation: str
    duplicate_matches: list[DuplicateMatch] = Field(default_factory=list)
    agent_outputs: list[AgentOutput] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))