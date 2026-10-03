from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from services.api.app import (
    app,
    get_diagnostic_orchestrator,
    get_diagnostic_service,
)
from shield.engines.repair_executor import ActionResult, ActionStatus
from shield.governance.decision import DecisionStatus, DiagnosticDecision
from shield.ingress.diagnostic_service import DiagnosticService
from shield.ingress.schemas import DiagnosticResult, Incident
from shield.orchestration.orchestrator import DiagnosticWorkflowResult

VALID_INCIDENT: dict[str, Any] = {
    "incident_id": "INC-001",
    "timestamp": "2026-09-26T12:00:00Z",
    "node_id": "node-a",
    "incident_type": "hardware",
    "severity": "high",
    "description": "NVLink degradation detected",
    "telemetry": {
        "link_errors": 42,
        "temperature": 72,
    },
    "metadata": {
        "cluster": "test-cluster",
    },
}


MOCK_DIAGNOSTIC_RESULT = DiagnosticResult(
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


def make_workflow_result(
    *,
    decision_status: DecisionStatus,
    confidence: float = 0.82,
) -> DiagnosticWorkflowResult:
    """Build a deterministic workflow result for API integration tests."""

    if decision_status == DecisionStatus.APPROVE:
        action_status = ActionStatus.EXECUTED
        action_message = "Repair action approved for execution."
    elif decision_status == DecisionStatus.REVIEW:
        action_status = ActionStatus.REQUIRES_REVIEW
        action_message = (
            "Repair requires human review before execution."
        )
    else:
        action_status = ActionStatus.BLOCKED
        action_message = "Repair blocked by governance decision."

    decision = DiagnosticDecision(
        incident_id="INC-001",
        status=decision_status,
        confidence=confidence,
        reason=f"Test decision: {decision_status.value}.",
        recommended_action="Collect NVLink health counters",
    )

    action = ActionResult(
        incident_id="INC-001",
        status=action_status,
        action="Collect NVLink health counters",
        message=action_message,
    )

    return DiagnosticWorkflowResult(
        diagnostic=MOCK_DIAGNOSTIC_RESULT,
        decision=decision,
        action=action,
    )


@pytest.fixture
def mock_diagnostic_service() -> MagicMock:
    """Provides an isolated mock for the diagnostic domain service."""

    service = MagicMock(spec=DiagnosticService)
    service.diagnose.return_value = MOCK_DIAGNOSTIC_RESULT
    return service


@pytest.fixture
def mock_orchestrator(
    mock_diagnostic_service: MagicMock,
) -> MagicMock:
    """Provides an isolated mock for the diagnostic orchestrator."""

    orchestrator = MagicMock()

    orchestrator.diagnose.return_value = MOCK_DIAGNOSTIC_RESULT

    orchestrator.run.return_value = make_workflow_result(
        decision_status=DecisionStatus.APPROVE,
    )

    return orchestrator


@pytest.fixture
def client(
    mock_diagnostic_service: MagicMock,
    mock_orchestrator: MagicMock,
) -> Generator[TestClient]:
    """TestClient with isolated service and orchestrator dependencies."""

    app.dependency_overrides[get_diagnostic_service] = (
        lambda: mock_diagnostic_service
    )
    app.dependency_overrides[get_diagnostic_orchestrator] = (
        lambda: mock_orchestrator
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestSystemEndpoints:
    def test_health_check_returns_ok_and_metadata(
        self,
        client: TestClient,
    ) -> None:
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "scd-shield"
        assert data["version"] == "1.0.0"

    @patch("services.api.app.configure_logging_from_settings")
    def test_create_app_configures_logging_from_settings(
        self,
        mock_configure_logging: MagicMock,
    ) -> None:
        from services.api.app import create_app
        from shield.config.settings import Settings

        settings = Settings(log_level="DEBUG")

        create_app(settings)

        mock_configure_logging.assert_called_once()
        configured_settings = mock_configure_logging.call_args.args[0]

        assert configured_settings.log_level == "DEBUG"


class TestDiagnoseEndpoint:
    def test_diagnose_valid_incident_success(
        self,
        client: TestClient,
        mock_diagnostic_service: MagicMock,
    ) -> None:
        response = client.post(
            "/diagnose",
            json=VALID_INCIDENT,
        )

        assert response.status_code == status.HTTP_200_OK

        body = response.json()

        assert body["incident_id"] == "INC-001"
        assert body["failure_family"] == "interconnect"
        assert body["affected_entity"] == "node-a"
        assert body["confidence"] == 0.82

        mock_diagnostic_service.diagnose.assert_called_once()

    @pytest.mark.parametrize(
        ("mutation", "expected_status"),
        [
            (
                {"confidence": 1.5},
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ),
            (
                {"confidence": -0.1},
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ),
            (
                {"unexpected_field": "disallowed"},
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ),
            (
                {"severity": "invalid_severity_level"},
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ),
            (
                {"incident_id": ""},
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ),
        ],
    )
    def test_diagnose_input_validation_errors(
        self,
        client: TestClient,
        mutation: dict[str, Any],
        expected_status: int,
    ) -> None:
        payload = {
            **VALID_INCIDENT,
            **mutation,
        }

        response = client.post(
            "/diagnose",
            json=payload,
        )

        assert response.status_code == expected_status

    def test_diagnose_handles_service_value_error(
        self,
        client: TestClient,
        mock_diagnostic_service: MagicMock,
    ) -> None:
        mock_diagnostic_service.diagnose.side_effect = ValueError(
            "Telemetry corrupted"
        )

        response = client.post(
            "/diagnose",
            json=VALID_INCIDENT,
        )

        assert response.status_code == (
            status.HTTP_422_UNPROCESSABLE_CONTENT
        )

        detail = response.json()["detail"]

        assert detail["error"] == "DiagnosticValidationError"
        assert detail["message"] == "Telemetry corrupted"
        assert detail["incident_id"] == "INC-001"

    def test_diagnose_value_error_includes_incident_id(
        self,
        client: TestClient,
        mock_diagnostic_service: MagicMock,
    ) -> None:
        mock_diagnostic_service.diagnose.side_effect = ValueError(
            "Telemetry corrupted"
        )

        response = client.post(
            "/diagnose",
            json=VALID_INCIDENT,
        )

        assert response.status_code == (
            status.HTTP_422_UNPROCESSABLE_CONTENT
        )

        detail = response.json()["detail"]

        assert detail["error"] == "DiagnosticValidationError"
        assert detail["message"] == "Telemetry corrupted"
        assert detail["incident_id"] == "INC-001"

    def test_diagnose_internal_error_includes_incident_id(
        self,
        client: TestClient,
        mock_diagnostic_service: MagicMock,
    ) -> None:
        mock_diagnostic_service.diagnose.side_effect = RuntimeError(
            "Unexpected diagnostic failure"
        )

        response = client.post(
            "/diagnose",
            json=VALID_INCIDENT,
        )

        assert response.status_code == (
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        detail = response.json()["detail"]

        assert detail["error"] == "DiagnosticExecutionError"
        assert detail["message"] == "Failed to evaluate incident."
        assert detail["incident_id"] == "INC-001"

    def test_diagnose_value_error_returns_structured_detail(
        self,
        client: TestClient,
        mock_diagnostic_service: MagicMock,
    ) -> None:
        mock_diagnostic_service.diagnose.side_effect = ValueError(
            "Telemetry corrupted"
        )

        response = client.post(
            "/diagnose",
            json=VALID_INCIDENT,
        )

        assert response.status_code == (
            status.HTTP_422_UNPROCESSABLE_CONTENT
        )

        detail = response.json()["detail"]

        assert set(detail) == {
            "error",
            "message",
            "incident_id",
        }

        assert detail["error"] == "DiagnosticValidationError"
        assert detail["message"] == "Telemetry corrupted"
        assert detail["incident_id"] == "INC-001"

    def test_diagnose_internal_error_does_not_expose_exception(
        self,
        client: TestClient,
        mock_diagnostic_service: MagicMock,
    ) -> None:
        mock_diagnostic_service.diagnose.side_effect = RuntimeError(
            "Database password leaked"
        )

        response = client.post(
            "/diagnose",
            json=VALID_INCIDENT,
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        detail = response.json()["detail"]

        assert detail["error"] == "DiagnosticExecutionError"
        assert detail["message"] == "Failed to evaluate incident."
        assert detail["incident_id"] == "INC-001"
        assert "Database password leaked" not in response.text

    def test_diagnose_service_receives_validated_incident(
        self,
        client: TestClient,
        mock_diagnostic_service: MagicMock,
    ) -> None:
        response = client.post(
            "/diagnose",
            json=VALID_INCIDENT,
        )

        assert response.status_code == status.HTTP_200_OK

        mock_diagnostic_service.diagnose.assert_called_once()

        incident = mock_diagnostic_service.diagnose.call_args.args[0]

        assert isinstance(incident, Incident)
        assert incident.incident_id == "INC-001"
        assert incident.node_id == "node-a"
        assert incident.telemetry["link_errors"] == 42


class TestDiagnosticWorkflowEndpoint:
    def test_workflow_approve_executes_action(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.run.return_value = make_workflow_result(
            decision_status=DecisionStatus.APPROVE,
        )

        response = client.post(
            "/diagnose/workflow",
            json=VALID_INCIDENT,
        )

        assert response.status_code == status.HTTP_200_OK

        body = response.json()

        assert body["diagnostic"]["incident_id"] == "INC-001"
        assert body["diagnostic"]["failure_family"] == "interconnect"

        assert body["decision"]["incident_id"] == "INC-001"
        assert body["decision"]["status"] == "approve"
        assert body["decision"]["confidence"] == 0.82

        assert body["action"]["incident_id"] == "INC-001"
        assert body["action"]["status"] == "executed"
        assert body["action"]["action"] == (
            "Collect NVLink health counters"
        )

        mock_orchestrator.run.assert_called_once()

    def test_workflow_review_requires_human_review(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.run.return_value = make_workflow_result(
            decision_status=DecisionStatus.REVIEW,
            confidence=0.65,
        )

        response = client.post(
            "/diagnose/workflow",
            json=VALID_INCIDENT,
        )

        assert response.status_code == status.HTTP_200_OK

        body = response.json()

        assert body["decision"]["status"] == "review"
        assert body["decision"]["confidence"] == 0.65
        assert body["action"]["status"] == "requires_review"
        assert body["action"]["message"] == (
            "Repair requires human review before execution."
        )

        mock_orchestrator.run.assert_called_once()

    def test_workflow_reject_blocks_action(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.run.return_value = make_workflow_result(
            decision_status=DecisionStatus.REJECT,
            confidence=0.40,
        )

        response = client.post(
            "/diagnose/workflow",
            json=VALID_INCIDENT,
        )

        assert response.status_code == status.HTTP_200_OK

        body = response.json()

        assert body["decision"]["status"] == "reject"
        assert body["decision"]["confidence"] == 0.40
        assert body["action"]["status"] == "blocked"
        assert body["action"]["message"] == (
            "Repair blocked by governance decision."
        )

        mock_orchestrator.run.assert_called_once()

    def test_workflow_passes_validated_incident_to_orchestrator(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        response = client.post(
            "/diagnose/workflow",
            json=VALID_INCIDENT,
        )

        assert response.status_code == status.HTTP_200_OK

        mock_orchestrator.run.assert_called_once()

        incident = mock_orchestrator.run.call_args.args[0]

        assert isinstance(incident, Incident)
        assert incident.incident_id == "INC-001"
        assert incident.node_id == "node-a"
        assert incident.telemetry["link_errors"] == 42

    @pytest.mark.parametrize(
        ("mutation", "expected_status"),
        [
            (
                {"incident_id": ""},
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ),
            (
                {"severity": "invalid_severity_level"},
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ),
            (
                {"unexpected_field": "disallowed"},
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ),
        ],
    )
    def test_workflow_input_validation_errors(
        self,
        client: TestClient,
        mutation: dict[str, Any],
        expected_status: int,
    ) -> None:
        payload = {
            **VALID_INCIDENT,
            **mutation,
        }

        response = client.post(
            "/diagnose/workflow",
            json=payload,
        )

        assert response.status_code == expected_status

    def test_workflow_handles_value_error(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.run.side_effect = ValueError(
            "Workflow validation failed"
        )

        response = client.post(
            "/diagnose/workflow",
            json=VALID_INCIDENT,
        )

        assert response.status_code == (
            status.HTTP_422_UNPROCESSABLE_CONTENT
        )

        detail = response.json()["detail"]

        assert detail["error"] == "DiagnosticValidationError"
        assert detail["message"] == "Workflow validation failed"
        assert detail["incident_id"] == "INC-001"

    def test_workflow_handles_internal_error_without_exposing_exception(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.run.side_effect = RuntimeError(
            "Database password leaked"
        )

        response = client.post(
            "/diagnose/workflow",
            json=VALID_INCIDENT,
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        detail = response.json()["detail"]

        assert detail["error"] == "DiagnosticExecutionError"
        assert detail["message"] == (
            "Failed to execute diagnostic workflow."
        )
        assert detail["incident_id"] == "INC-001"
        assert "Database password leaked" not in response.text

    def test_workflow_response_rejects_extra_fields_from_mocked_models(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        workflow = make_workflow_result(
            decision_status=DecisionStatus.APPROVE,
        )

        assert workflow.decision.status == DecisionStatus.APPROVE
        assert workflow.action.status == ActionStatus.EXECUTED

        mock_orchestrator.run.return_value = workflow

        response = client.post(
            "/diagnose/workflow",
            json=VALID_INCIDENT,
        )

        assert response.status_code == status.HTTP_200_OK
        assert set(response.json()) == {
            "diagnostic",
            "decision",
            "action",}