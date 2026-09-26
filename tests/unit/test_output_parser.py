import pytest

from shield.ingress.output_parser import DiagnosticOutputParser

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


def test_parse_valid_diagnostic_output():
    parser = DiagnosticOutputParser()

    result = parser.parse(VALID_OUTPUT)

    assert result.incident_id == "INC-001"
    assert result.failure_family == "interconnect"
    assert result.confidence == 0.82


def test_invalid_json_is_rejected():
    parser = DiagnosticOutputParser()

    with pytest.raises(ValueError, match="valid JSON"):
        parser.parse("{not valid json")


def test_schema_invalid_output_is_rejected():
    parser = DiagnosticOutputParser()

    invalid_output = """
    {
        "incident_id": "INC-001",
        "failure_family": "interconnect",
        "affected_entity": "node-a",
        "primary_hypothesis": "NVLink degradation",
        "confidence": 1.5,
        "recommended_action": "Investigate"
    }
    """

    with pytest.raises(ValueError, match="schema validation"):
        parser.parse(invalid_output)


def test_unexpected_output_field_is_rejected():
    parser = DiagnosticOutputParser()

    invalid_output = """
    {
        "incident_id": "INC-001",
        "failure_family": "interconnect",
        "affected_entity": "node-a",
        "primary_hypothesis": "NVLink degradation",
        "alternative_hypotheses": [],
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "missing_evidence": [],
        "confidence": 0.8,
        "recommended_action": "Investigate",
        "invented_field": "should fail"
    }
    """

    with pytest.raises(ValueError, match="schema validation"):
        parser.parse(invalid_output)
