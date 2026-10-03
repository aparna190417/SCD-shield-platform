from unittest.mock import MagicMock

from shield.engines.repair_executor import ActionStatus
from shield.governance.decision import DecisionStatus
from shield.ingress.diagnostic_service import DiagnosticService
from shield.ingress.schemas import DiagnosticResult, Incident
from shield.orchestration.orchestrator import DiagnosticOrchestrator


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


def make_result() -> DiagnosticResult:
    return DiagnosticResult(
        incident_id="INC-001",
        failure_family="interconnect",
        affected_entity="node-a",
        primary_hypothesis="NVLink degradation",
        alternative_hypotheses=["Transient communication fault"],
        supporting_evidence=["link_errors=42"],
        contradicting_evidence=[],
        missing_evidence=["NVLink health counters"],
        confidence=0.82,
        recommended_action="Collect NVLink health counters",
    )


def test_orchestrator_delegates_to_diagnostic_service() -> None:
    service = MagicMock(spec=DiagnosticService)
    service.diagnose.return_value = make_result()

    orchestrator = DiagnosticOrchestrator(service)

    result = orchestrator.diagnose(
        make_incident(),
        prompt_version="v1",
        hardware_context="A100 GPU node",
        retrieved_evidence="NVLink documentation",
        incident_history="No previous incidents",
    )

    assert result.incident_id == "INC-001"

    service.diagnose.assert_called_once_with(
        make_incident(),
        prompt_version="v1",
        hardware_context="A100 GPU node",
        retrieved_evidence="NVLink documentation",
        incident_history="No previous incidents",
    )


def test_orchestrator_uses_context_builder() -> None:
    service = MagicMock(spec=DiagnosticService)
    service.diagnose.return_value = make_result()

    def build_context(incident: Incident) -> dict[str, str]:
        assert incident.incident_id == "INC-001"

        return {
            "hardware_context": "H100 GPU node",
            "retrieved_evidence": "Known NVLink failure pattern",
            "incident_history": "Two previous incidents",
        }

    orchestrator = DiagnosticOrchestrator(
        service,
        context_builder=build_context,
    )

    result = orchestrator.diagnose(make_incident())

    assert result.incident_id == "INC-001"

    service.diagnose.assert_called_once_with(
        make_incident(),
        prompt_version="v1",
        hardware_context="H100 GPU node",
        retrieved_evidence="Known NVLink failure pattern",
        incident_history="Two previous incidents",
    )


def test_orchestrator_context_preserves_explicit_values_when_missing() -> None:
    service = MagicMock(spec=DiagnosticService)
    service.diagnose.return_value = make_result()

    def build_context(_: Incident) -> dict[str, str]:
        return {
            "hardware_context": "GPU node",
        }

    orchestrator = DiagnosticOrchestrator(
        service,
        context_builder=build_context,
    )

    orchestrator.diagnose(
        make_incident(),
        hardware_context="Fallback hardware",
        retrieved_evidence="Provided evidence",
        incident_history="Provided history",
    )

    service.diagnose.assert_called_once_with(
        make_incident(),
        prompt_version="v1",
        hardware_context="GPU node",
        retrieved_evidence="Provided evidence",
        incident_history="Provided history",
    )


def test_orchestrator_run_approves_and_executes() -> None:
    service = MagicMock(spec=DiagnosticService)
    service.diagnose.return_value = make_result()

    orchestrator = DiagnosticOrchestrator(service)

    workflow = orchestrator.run(
        make_incident(),
        hardware_context="A100 GPU node",
        retrieved_evidence="NVLink evidence",
        incident_history="No previous incidents",
    )

    assert workflow.diagnostic.incident_id == "INC-001"
    assert workflow.decision.status == DecisionStatus.APPROVE
    assert workflow.action.status == ActionStatus.EXECUTED
    assert workflow.action.incident_id == "INC-001"


def test_orchestrator_run_blocks_low_confidence_workflow() -> None:
    service = MagicMock(spec=DiagnosticService)

    low_confidence_result = make_result().model_copy(
        update={"confidence": 0.40}
    )

    service.diagnose.return_value = low_confidence_result

    orchestrator = DiagnosticOrchestrator(service)

    workflow = orchestrator.run(make_incident())

    assert workflow.diagnostic.confidence == 0.40
    assert workflow.decision.status == DecisionStatus.REJECT
    assert workflow.action.status == ActionStatus.BLOCKED


def test_orchestrator_run_requires_review_for_medium_confidence() -> None:
    service = MagicMock(spec=DiagnosticService)

    review_result = make_result().model_copy(
        update={"confidence": 0.70}
    )

    service.diagnose.return_value = review_result

    orchestrator = DiagnosticOrchestrator(service)

    workflow = orchestrator.run(make_incident())

    assert workflow.diagnostic.confidence == 0.70
    assert workflow.decision.status == DecisionStatus.REVIEW
    assert workflow.action.status == ActionStatus.REQUIRES_REVIEW