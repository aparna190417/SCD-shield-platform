from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Incident(BaseModel):
    """Incoming cluster incident."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    timestamp: datetime
    node_id: str = Field(min_length=1)
    incident_type: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    description: str = Field(min_length=1)

    telemetry: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiagnosticResult(BaseModel):
    """Structured result produced by the diagnostic pipeline."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str
    root_cause: str
    failure_family: str
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_action: str
    evidence: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""