from datetime import UTC, datetime
from typing import Any

import pytest

from shield.ingress.diagnostic_service import DiagnosticService
from shield.ingress.llm_adapter import FakeLLMAdapter, LLMRequest
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


class RecordingRetriever:
    """Evidence retriever double that records service interactions."""

    def __init__(self) -> None:
        self.retrieve_calls: list[Incident] = []
        self.format_calls: list[list[Any]] = []

    def retrieve(self, incident: Incident) -> list[Any]:
        self.retrieve_calls.append(incident)
        return [
            {
                "evidence_id": "EV-TEST",
                "summary": "Test evidence",
            }
        ]

    def format_results(self, results: list[Any]) -> str:
        self.format_calls.append(results)
        return "[EV-TEST] Test evidence"


def test_diagnostic_service_returns_result() -> None:
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


def test_diagnostic_service_repairs_invalid_first_response() -> None:
    class SequenceLLMAdapter:
        def __init__(self) -> None:
            self.responses = [
                "{invalid json}",
                VALID_OUTPUT,
            ]
            self.requests: list[LLMRequest] = []

        def generate(self, request: LLMRequest) -> str:
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

    repair_prompt = adapter.requests[1].prompt

    assert "Repair the previous output" in repair_prompt.developer
    assert "only valid structured JSON" in repair_prompt.developer


def test_diagnostic_service_injects_retrieved_evidence() -> None:
    adapter = FakeLLMAdapter(VALID_OUTPUT)

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    service.diagnose(make_incident())

    assert len(adapter.requests) == 1

    rendered_prompt = adapter.requests[0].prompt

    assert "[EV-001]" in rendered_prompt.user
    assert "increased link errors" in rendered_prompt.user


def test_diagnostic_service_uses_provided_retrieved_evidence() -> None:
    adapter = FakeLLMAdapter(VALID_OUTPUT)
    retriever = RecordingRetriever()

    service = DiagnosticService(
        llm_adapter=adapter,
        evidence_retriever=retriever,
    )

    service.diagnose(
        make_incident(),
        retrieved_evidence="MANUALLY PROVIDED EVIDENCE",
    )

    rendered_prompt = adapter.requests[0].prompt

    assert "MANUALLY PROVIDED EVIDENCE" in rendered_prompt.user
    assert "[EV-TEST]" not in rendered_prompt.user
    assert retriever.retrieve_calls == []
    assert retriever.format_calls == []


def test_diagnostic_service_retrieves_and_formats_evidence_when_not_provided() -> None:
    adapter = FakeLLMAdapter(VALID_OUTPUT)
    retriever = RecordingRetriever()
    incident = make_incident()

    service = DiagnosticService(
        llm_adapter=adapter,
        evidence_retriever=retriever,
    )

    service.diagnose(incident)

    assert retriever.retrieve_calls == [incident]
    assert len(retriever.format_calls) == 1

    rendered_prompt = adapter.requests[0].prompt

    assert "[EV-TEST] Test evidence" in rendered_prompt.user


def test_diagnostic_service_passes_prompt_version_to_registry() -> None:
    adapter = FakeLLMAdapter(VALID_OUTPUT)

    class RecordingPromptRegistry:
        def __init__(self) -> None:
            self.versions: list[str] = []

        def load_prompt_bundle(self, version: str) -> Any:
            self.versions.append(version)

            class Bundle:
                system = "System"
                developer = "Developer"
                user = (
                    "Incident: {incident}\n"
                    "Telemetry: {telemetry}\n"
                    "Hardware: {hardware_context}\n"
                    "Evidence: {retrieved_evidence}\n"
                    "History: {incident_history}"
                )

            return Bundle()

    registry = RecordingPromptRegistry()

    service = DiagnosticService(
        llm_adapter=adapter,
        prompt_registry=registry,
    )

    service.diagnose(
        make_incident(),
        prompt_version="v1",
    )

    assert registry.versions == ["v1"]


def test_diagnostic_service_propagates_evidence_retrieval_failure() -> None:
    adapter = FakeLLMAdapter(VALID_OUTPUT)

    class FailingRetriever:
        def retrieve(self, incident: Incident) -> list[Any]:
            raise RuntimeError("Evidence store unavailable")

        def format_results(self, results: list[Any]) -> str:
            raise AssertionError("format_results should not be called")

    service = DiagnosticService(
        llm_adapter=adapter,
        evidence_retriever=FailingRetriever(),
    )

    with pytest.raises(
        RuntimeError,
        match="Evidence store unavailable",
    ):
        service.diagnose(make_incident())

    assert len(adapter.requests) == 0


def test_diagnostic_service_propagates_initial_llm_failure() -> None:
    class FailingLLMAdapter:
        def __init__(self) -> None:
            self.requests: list[LLMRequest] = []

        def generate(self, request: LLMRequest) -> str:
            self.requests.append(request)
            raise RuntimeError("LLM unavailable")

    adapter = FailingLLMAdapter()

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    with pytest.raises(
        RuntimeError,
        match="LLM unavailable",
    ):
        service.diagnose(
            make_incident(),
            retrieved_evidence="Known evidence",
        )

    assert len(adapter.requests) == 1


def test_diagnostic_service_propagates_repair_llm_failure() -> None:
    class RepairFailingLLMAdapter:
        def __init__(self) -> None:
            self.responses = ["{invalid json}"]
            self.requests: list[LLMRequest] = []

        def generate(self, request: LLMRequest) -> str:
            self.requests.append(request)

            if len(self.requests) == 1:
                return self.responses[0]

            raise RuntimeError("Repair LLM unavailable")

    adapter = RepairFailingLLMAdapter()

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    with pytest.raises(
        RuntimeError,
        match="Repair LLM unavailable",
    ):
        service.diagnose(
            make_incident(),
            retrieved_evidence="Known evidence",
        )

    assert len(adapter.requests) == 2
    assert "Repair the previous output" in adapter.requests[1].prompt.developer


def test_diagnostic_service_preserves_incident_context_in_prompt() -> None:
    adapter = FakeLLMAdapter(VALID_OUTPUT)

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    service.diagnose(
        make_incident(),
        hardware_context="A100 GPU node",
        retrieved_evidence="NVLink documentation",
        incident_history="No previous matching incidents",
    )

    prompt = adapter.requests[0].prompt

    assert "INC-001" in prompt.user
    assert "link_errors" in prompt.user
    assert "A100 GPU node" in prompt.user
    assert "NVLink documentation" in prompt.user
    assert "No previous matching incidents" in prompt.user

def test_diagnostic_service_logs_start_and_completion(
    caplog: pytest.LogCaptureFixture,
) -> None:
    adapter = FakeLLMAdapter(VALID_OUTPUT)

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    with caplog.at_level("INFO"):
        result = service.diagnose(
            make_incident(),
            retrieved_evidence="Known evidence",
        )

    assert result.incident_id == "INC-001"

    messages = [record.message for record in caplog.records]

    assert "Starting diagnostic" in messages
    assert "Sending initial diagnostic request" in messages
    assert "Diagnostic completed" in messages


def test_diagnostic_service_logs_incident_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    adapter = FakeLLMAdapter(VALID_OUTPUT)

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    with caplog.at_level("INFO"):
        service.diagnose(
            make_incident(),
            retrieved_evidence="Known evidence",
        )

    diagnostic_records = [
        record
        for record in caplog.records
        if record.name == "shield.ingress.diagnostic_service"
    ]

    assert diagnostic_records
    assert all(
        getattr(record, "incident_id", None) == "INC-001"
        for record in diagnostic_records
    )


def test_diagnostic_service_logs_evidence_retrieval(
    caplog: pytest.LogCaptureFixture,
) -> None:
    adapter = FakeLLMAdapter(VALID_OUTPUT)

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    with caplog.at_level("INFO"):
        service.diagnose(make_incident())

    messages = [record.message for record in caplog.records]

    assert "Evidence retrieval completed" in messages

    retrieval_record = next(
        record
        for record in caplog.records
        if record.message == "Evidence retrieval completed"
    )

    assert retrieval_record.incident_id == "INC-001"
    assert retrieval_record.evidence_count >= 0


def test_diagnostic_service_logs_repair_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class SequenceLLMAdapter:
        def __init__(self) -> None:
            self.responses = [
                "{invalid json}",
                VALID_OUTPUT,
            ]
            self.requests: list[LLMRequest] = []

        def generate(self, request: LLMRequest) -> str:
            self.requests.append(request)
            return self.responses.pop(0)

    adapter = SequenceLLMAdapter()

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    with caplog.at_level("WARNING"):
        result = service.diagnose(
            make_incident(),
            retrieved_evidence="Known evidence",
        )

    assert result.incident_id == "INC-001"

    repair_records = [
        record
        for record in caplog.records
        if record.message == "Repairing diagnostic response"
    ]

    assert len(repair_records) == 1
    assert repair_records[0].incident_id == "INC-001"


def test_diagnostic_service_does_not_log_raw_llm_output(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret_response = (
        '{"incident_id":"INC-001",'
        '"primary_hypothesis":"SECRET_MODEL_OUTPUT"}'
    )

    adapter = FakeLLMAdapter(secret_response)

    service = DiagnosticService(
        llm_adapter=adapter,
    )

    with caplog.at_level("DEBUG"):
        try:
            service.diagnose(
                make_incident(),
                retrieved_evidence="Known evidence",
            )
        except Exception:
            pass

    logged_text = caplog.text

    assert secret_response not in logged_text
    assert "SECRET_MODEL_OUTPUT" not in logged_text