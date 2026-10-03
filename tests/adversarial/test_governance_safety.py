from shield.governance.decision import DecisionEngine, DecisionStatus
from shield.ingress.schemas import DiagnosticResult, Incident


def make_incident(
    *,
    incident_id: str = "INC-ADV-001",
    severity: str = "high",
    temperature: float = 50,
    temperature_limit: float = 100,
    power_w: float = 200,
    power_limit_w: float = 500,
) -> Incident:
    return Incident(
        incident_id=incident_id,
        timestamp="2026-10-03T12:00:00Z",
        node_id="node-a",
        incident_type="hardware",
        severity=severity,
        description="Adversarial governance test incident",
        telemetry={
            "temperature": temperature,
            "temperature_limit": temperature_limit,
            "power_w": power_w,
            "power_limit_w": power_limit_w,
        },
        metadata={},
    )


def make_diagnostic(
    *,
    incident_id: str = "INC-ADV-001",
    confidence: float = 0.99,
) -> DiagnosticResult:
    return DiagnosticResult(
        incident_id=incident_id,
        failure_family="thermal",
        affected_entity="node-a",
        primary_hypothesis="Thermal overload",
        alternative_hypotheses=[],
        supporting_evidence=["temperature telemetry"],
        contradicting_evidence=[],
        missing_evidence=[],
        confidence=confidence,
        recommended_action="Reduce workload",
    )


def test_critical_telemetry_cannot_be_auto_approved() -> None:
    engine = DecisionEngine()

    incident = make_incident(
        severity="critical",
        temperature=100,
        temperature_limit=100,
    )

    diagnostic = make_diagnostic()

    decision = engine.evaluate(incident, diagnostic)

    assert decision.status == DecisionStatus.REJECT
    assert "CPTP" in decision.reason


def test_warning_telemetry_cannot_bypass_human_review() -> None:
    engine = DecisionEngine()

    incident = make_incident(
        severity="high",
        temperature=80,
        temperature_limit=100,
    )

    diagnostic = make_diagnostic()

    decision = engine.evaluate(incident, diagnostic)

    assert decision.status == DecisionStatus.REVIEW
    assert "CPTP" in decision.reason


def test_high_confidence_cannot_override_critical_cptp() -> None:
    engine = DecisionEngine()

    incident = make_incident(
        severity="critical",
        temperature=100,
        temperature_limit=100,
    )

    diagnostic = make_diagnostic(confidence=1.0)

    decision = engine.evaluate(incident, diagnostic)

    assert decision.confidence == 1.0
    assert decision.status == DecisionStatus.REJECT


def test_power_limit_violation_cannot_be_approved() -> None:
    engine = DecisionEngine()

    incident = make_incident(
        severity="critical",
        temperature=50,
        temperature_limit=100,
        power_w=500,
        power_limit_w=500,
    )

    diagnostic = make_diagnostic()

    decision = engine.evaluate(incident, diagnostic)

    assert decision.status == DecisionStatus.REJECT
    assert "CPTP" in decision.reason


def test_safe_telemetry_allows_high_confidence_approval() -> None:
    engine = DecisionEngine()

    incident = make_incident(
        severity="high",
        temperature=50,
        temperature_limit=100,
        power_w=200,
        power_limit_w=500,
    )

    diagnostic = make_diagnostic(confidence=0.95)

    decision = engine.evaluate(incident, diagnostic)

    assert decision.status == DecisionStatus.APPROVE