import pytest

from shield.ingress.repair import DiagnosticRepairEngine

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
    "missing_evidence": [],
    "confidence": 0.82,
    "recommended_action": "Collect NVLink health counters"
}
"""


def test_valid_output_requires_no_repair():
    engine = DiagnosticRepairEngine(max_attempts=2)

    def repair_should_not_run(_: str) -> str:
        raise AssertionError("Repair should not be called.")

    result = engine.parse_with_repair(
        VALID_OUTPUT,
        repair_should_not_run,
    )

    assert result.result.incident_id == "INC-001"
    assert result.attempts == 1


def test_invalid_output_is_repaired():
    engine = DiagnosticRepairEngine(max_attempts=2)

    calls = []

    def repair_output(raw_output: str) -> str:
        calls.append(raw_output)
        return VALID_OUTPUT

    result = engine.parse_with_repair(
        "{invalid json}",
        repair_output,
    )

    assert result.result.incident_id == "INC-001"
    assert result.attempts == 2
    assert len(calls) == 1


def test_retry_limit_is_respected():
    engine = DiagnosticRepairEngine(max_attempts=2)

    calls = []

    def failed_repair(raw_output: str) -> str:
        calls.append(raw_output)
        return "{still invalid}"

    with pytest.raises(ValueError, match="valid JSON"):
        engine.parse_with_repair(
            "{invalid json}",
            failed_repair,
        )

    assert len(calls) == 1


def test_invalid_max_attempts_is_rejected():
    with pytest.raises(ValueError, match="at least 1"):
        DiagnosticRepairEngine(max_attempts=0)
