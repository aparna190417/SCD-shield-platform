import pytest

from shield.governance.decision import (
    DecisionEngine,
    DecisionStatus,
)
from shield.ingress.schemas import DiagnosticResult, Incident


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


def make_result(
    *,
    confidence: float = 0.82,
    incident_id: str = "INC-001",
) -> DiagnosticResult:
    return DiagnosticResult(
        incident_id=incident_id,
        failure_family="interconnect",
        affected_entity="node-a",
        primary_hypothesis="NVLink degradation",
        alternative_hypotheses=["Transient communication fault"],
        supporting_evidence=["link_errors=42"],
        contradicting_evidence=[],
        missing_evidence=[],
        confidence=confidence,
        recommended_action="Collect NVLink health counters",
    )


def test_high_confidence_diagnostic_is_approved() -> None:
    engine = DecisionEngine()

    decision = engine.evaluate(
        make_incident(),
        make_result(confidence=0.90),
    )

    assert decision.status == DecisionStatus.APPROVE
    assert decision.incident_id == "INC-001"
    assert decision.confidence == 0.90


def test_medium_confidence_diagnostic_requires_review() -> None:
    engine = DecisionEngine()

    decision = engine.evaluate(
        make_incident(),
        make_result(confidence=0.70),
    )

    assert decision.status == DecisionStatus.REVIEW
    assert "human review" in decision.reason


def test_low_confidence_diagnostic_is_rejected() -> None:
    engine = DecisionEngine()

    decision = engine.evaluate(
        make_incident(),
        make_result(confidence=0.40),
    )

    assert decision.status == DecisionStatus.REJECT
    assert "below the review threshold" in decision.reason


def test_incident_id_mismatch_is_rejected() -> None:
    engine = DecisionEngine()

    decision = engine.evaluate(
        make_incident(),
        make_result(incident_id="INC-999"),
    )

    assert decision.status == DecisionStatus.REJECT
    assert "does not match" in decision.reason


@pytest.mark.parametrize(
    "kwargs",
    [
        {"approval_threshold": -0.1},
        {"approval_threshold": 1.1},
        {"review_threshold": -0.1},
        {"review_threshold": 1.1},
        {
            "approval_threshold": 0.60,
            "review_threshold": 0.80,
        },
    ],
)
def test_invalid_thresholds_are_rejected(
    kwargs: dict[str, float],
) -> None:
    with pytest.raises(ValueError):
        DecisionEngine(**kwargs)