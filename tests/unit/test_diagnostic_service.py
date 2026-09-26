from datetime import UTC, datetime

from shield.ingress.diagnostic_service import DiagnosticService
from shield.ingress.llm_adapter import FakeLLMAdapter
from shield.ingress.schemas import Incident

VALID_OUTPUT = """
{
    "incident_id": "INC-001",
    "failure_family": "interconnect",
    "affected_entity": "node-a",
    "primary_hypothesis": "NVLink degradation",
    "alternative_hypotheses": [
        "Transient communication fault"
    ],
    "supporting_evidence": [
        "link_errors=42"
    ],
    "contradicting_evidence": [],
    "missing_evidence": [
        "NVLink health counters"
    ],
    "confidence": 0.82,
    "recommended_action": "Collect NVLink health counters"
}
"""


def make_incident() -> Incident:
    return Incident(
        incident_id="INC-001",
        timestamp=datetime.now(UTC),
        node_id="node-a",
        incident_type="hardware",
        severity="high",
        description="NVLink degradation detected",
        telemetry={
            "link_errors": 42,
            "temperature": 72,
        },
        metadata={
            "cluster": "test-cluster",
        },
    )


def test_diagnostic_service_returns_result():
    adapter = FakeLLMAdapter(VALID_OUTPUT)

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    result = service.diagnose(
        make_incident(),
        hardware_context="A100 GPU node",
        retrieved_evidence="NVLink documentation",
        incident_history="No previous matching incidents",
    )

    assert result.incident_id == "INC-001"
    assert result.failure_family == "interconnect"
    assert result.confidence == 0.82

    assert len(adapter.requests) == 1


def test_diagnostic_service_repairs_invalid_first_response():
    class SequenceLLMAdapter:
        def __init__(self):
            self.responses = [
                "{invalid json}",
                VALID_OUTPUT,
            ]
            self.requests = []

        def generate(self, request):
            self.requests.append(request)
            return self.responses.pop(0)

    adapter = SequenceLLMAdapter()

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    result = service.diagnose(make_incident())

    assert result.incident_id == "INC-001"
    assert result.confidence == 0.82
    assert len(adapter.requests) == 2
