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

def test_critical_cptp_rejects_even_with_high_confidence() -> None:
    engine = DecisionEngine()

    incident = Incident(
        incident_id="INC-CPTP-CRITICAL",
        timestamp="2026-09-26T12:00:00Z",
        node_id="node-a",
        incident_type="hardware",
        severity="critical",
        description="Critical thermal condition",
        telemetry={
            "temperature": 95,
            "temperature_limit": 100,
            "power_w": 300,
            "power_limit_w": 500,
        },
        metadata={},
    )

    diagnostic = DiagnosticResult(
        incident_id="INC-CPTP-CRITICAL",
        failure_family="thermal",
        affected_entity="node-a",
        primary_hypothesis="Thermal overload",
        alternative_hypotheses=[],
        supporting_evidence=["temperature=95"],
        contradicting_evidence=[],
        missing_evidence=[],
        confidence=0.99,
        recommended_action="Reduce workload",
    )

    decision = engine.evaluate(incident, diagnostic)

    assert decision.status == DecisionStatus.REJECT
    assert "CPTP" in decision.reason


def test_warning_cptp_requires_review() -> None:
    engine = DecisionEngine()

    incident = Incident(
        incident_id="INC-CPTP-WARNING",
        timestamp="2026-09-26T12:00:00Z",
        node_id="node-a",
        incident_type="hardware",
        severity="high",
        description="Thermal warning",
        telemetry={
            "temperature": 80,
            "temperature_limit": 100,
            "power_w": 300,
            "power_limit_w": 500,
        },
        metadata={},
    )

    diagnostic = DiagnosticResult(
        incident_id="INC-CPTP-WARNING",
        failure_family="thermal",
        affected_entity="node-a",
        primary_hypothesis="Thermal pressure",
        alternative_hypotheses=[],
        supporting_evidence=["temperature=80"],
        contradicting_evidence=[],
        missing_evidence=[],
        confidence=0.99,
        recommended_action="Reduce workload",
    )

    decision = engine.evaluate(incident, diagnostic)

    assert decision.status == DecisionStatus.REVIEW
    assert "CPTP" in decision.reason


def test_normal_cptp_allows_high_confidence_approval() -> None:
    engine = DecisionEngine()

    incident = Incident(
        incident_id="INC-CPTP-NORMAL",
        timestamp="2026-09-26T12:00:00Z",
        node_id="node-a",
        incident_type="hardware",
        severity="high",
        description="Normal operating conditions",
        telemetry={
            "temperature": 50,
            "temperature_limit": 100,
            "power_w": 200,
            "power_limit_w": 500,
        },
        metadata={},
    )

    diagnostic = DiagnosticResult(
        incident_id="INC-CPTP-NORMAL",
        failure_family="interconnect",
        affected_entity="node-a",
        primary_hypothesis="NVLink degradation",
        alternative_hypotheses=[],
        supporting_evidence=["link_errors=42"],
        contradicting_evidence=[],
        missing_evidence=[],
        confidence=0.95,
        recommended_action="Collect NVLink health counters",
    )

    decision = engine.evaluate(incident, diagnostic)

    assert decision.status == DecisionStatus.APPROVE
    assert decision.confidence == 0.95