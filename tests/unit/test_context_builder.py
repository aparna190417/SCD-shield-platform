import pytest

from shield.context.builder import IncidentContextBuilder
from shield.ingress.schemas import Incident
from shield.retrieval.models import EvidenceRecord
from shield.retrieval.retriever import EvidenceRetriever
from shield.retrieval.store import LocalEvidenceStore


def make_incident() -> Incident:
    return Incident(
        incident_id="INC-001",
        timestamp="2026-09-26T12:00:00Z",
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


def test_context_builder_returns_required_context() -> None:
    builder = IncidentContextBuilder()

    context = builder.build(make_incident())

    assert set(context) == {
        "hardware_context",
        "retrieved_evidence",
        "incident_history",
    }

    assert "node-a" in context["hardware_context"]
    assert "hardware" in context["hardware_context"]
    assert "high" in context["hardware_context"]

    assert "EV-001" in context["retrieved_evidence"]
    assert "NVLink incidents" in context["retrieved_evidence"]

    assert "INC-001" in context["incident_history"]


def test_context_builder_respects_retrieval_limit() -> None:
    records = [
        EvidenceRecord(
            evidence_id=f"EV-{index:03d}",
            incident_type="hardware",
            node_id="node-a",
            text=f"Hardware evidence {index}",
            tags=("hardware",),
        )
        for index in range(1, 5)
    ]

    retriever = EvidenceRetriever(
        LocalEvidenceStore(records),
    )

    builder = IncidentContextBuilder(
        retriever,
        retrieval_limit=2,
    )

    context = builder.build(make_incident())

    evidence_lines = context["retrieved_evidence"].splitlines()

    assert len(evidence_lines) == 2


def test_context_builder_rejects_invalid_retrieval_limit() -> None:
    with pytest.raises(ValueError, match="retrieval_limit"):
        IncidentContextBuilder(retrieval_limit=0)