from datetime import datetime

import pytest
from pydantic import ValidationError

from shield.ingress.schemas import DiagnosticResult, Incident


def test_valid_incident():
    incident = Incident(
        incident_id="INC-001",
        timestamp=datetime(2026, 9, 26, 20, 0, 0),
        node_id="node-a",
        incident_type="nvlink_degradation",
        severity="high",
        description="NVLink error rate increased",
        telemetry={"link_errors": 42},
    )

    assert incident.incident_id == "INC-001"
    assert incident.node_id == "node-a"


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValidationError):
        DiagnosticResult(
            incident_id="INC-001",
            root_cause="NVLink degradation",
            failure_family="interconnect",
            confidence=1.5,
            recommended_action="Investigate NVLink health",
        )


def test_unexpected_incident_field_is_rejected():
    with pytest.raises(ValidationError):
        Incident(
            incident_id="INC-001",
            timestamp=datetime(2026, 9, 26, 20, 0, 0),
            node_id="node-a",
            incident_type="nvlink_degradation",
            severity="high",
            description="NVLink error rate increased",
            unexpected_field="should_fail",)