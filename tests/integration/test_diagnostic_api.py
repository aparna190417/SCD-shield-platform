from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from services.api.app import app, get_diagnostic_service
from shield.ingress.diagnostic_service import DiagnosticService
from shield.ingress.schemas import DiagnosticResult

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


@pytest.fixture
def mock_diagnostic_service() -> MagicMock:
    """Provides an isolated mock for the diagnostic domain service."""
    service = MagicMock(spec=DiagnosticService)
    service.diagnose.return_value = MOCK_DIAGNOSTIC_RESULT
    return service


@pytest.fixture
def client(mock_diagnostic_service: MagicMock) -> Generator[TestClient]:
    """TestClient fixture with dependency overrides and lifespan management."""
    app.dependency_overrides[get_diagnostic_service] = lambda: mock_diagnostic_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestSystemEndpoints:
    def test_health_check_returns_ok_and_metadata(self, client: TestClient) -> None:
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestDiagnoseEndpoint:
    def test_diagnose_valid_incident_success(
        self,
        client: TestClient,
        mock_diagnostic_service: MagicMock,
    ) -> None:
        response = client.post("/diagnose", json=VALID_INCIDENT)

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
            ({"confidence": 1.5}, status.HTTP_422_UNPROCESSABLE_CONTENT),
            ({"confidence": -0.1}, status.HTTP_422_UNPROCESSABLE_CONTENT),
            ({"unexpected_field": "disallowed"}, status.HTTP_422_UNPROCESSABLE_CONTENT),
            (
                {"severity": "invalid_severity_level"},
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ),
            ({"incident_id": ""}, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ],
    )
    def test_diagnose_input_validation_errors(
        self,
        client: TestClient,
        mutation: dict[str, Any],
        expected_status: int,
    ) -> None:
        payload = {**VALID_INCIDENT, **mutation}
        response = client.post("/diagnose", json=payload)

        assert response.status_code == expected_status

    def test_diagnose_handles_service_value_error(
        self,
        client: TestClient,
        mock_diagnostic_service: MagicMock,
    ) -> None:
        mock_diagnostic_service.diagnose.side_effect = ValueError("Telemetry corrupted")

        response = client.post("/diagnose", json=VALID_INCIDENT)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"]["error"] == "DiagnosticValidationError"
