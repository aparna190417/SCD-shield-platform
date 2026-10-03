from shield.engines.repair_executor import (
    ActionStatus,
    RepairExecutor,
)
from shield.governance.decision import (
    DecisionStatus,
    DiagnosticDecision,
)


def make_decision(
    status: DecisionStatus,
    *,
    incident_id: str = "INC-001",
) -> DiagnosticDecision:
    return DiagnosticDecision(
        incident_id=incident_id,
        status=status,
        confidence=0.90,
        reason="Test governance decision.",
        recommended_action="Collect NVLink health counters",
    )


def test_approved_decision_allows_execution_boundary() -> None:
    executor = RepairExecutor()

    result = executor.execute(
        make_decision(DecisionStatus.APPROVE),
    )

    assert result.incident_id == "INC-001"
    assert result.status == ActionStatus.EXECUTED
    assert result.action == "Collect NVLink health counters"


def test_review_decision_requires_human_review() -> None:
    executor = RepairExecutor()

    result = executor.execute(
        make_decision(DecisionStatus.REVIEW),
    )

    assert result.status == ActionStatus.REQUIRES_REVIEW
    assert "human review" in result.message


def test_rejected_decision_blocks_execution() -> None:
    executor = RepairExecutor()

    result = executor.execute(
        make_decision(DecisionStatus.REJECT),
    )

    assert result.status == ActionStatus.BLOCKED
    assert "blocked" in result.message