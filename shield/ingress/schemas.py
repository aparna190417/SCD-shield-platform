from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Incident(BaseModel):
    """Incoming cluster incident."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    timestamp: datetime
    node_id: str = Field(min_length=1)
    incident_type: str = Field(min_length=1)
    severity: Literal["low", "medium", "high", "critical"]
    description: str = Field(min_length=1)

    telemetry: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiagnosticResult(BaseModel):
    """Validated structured diagnostic result."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    failure_family: str = Field(min_length=1)
    affected_entity: str = Field(min_length=1)

    primary_hypothesis: str = Field(min_length=1)
    alternative_hypotheses: list[str] = Field(default_factory=list)

    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)

    confidence: float = Field(ge=0.0, le=1.0)

    recommended_action: str = Field(min_length=1)
