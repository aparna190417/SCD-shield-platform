from shield.ingress.schemas import Incident
from shield.retrieval.retriever import EvidenceRetriever


def make_incident() -> Incident:
    return Incident.model_validate(
        {
            "incident_id": "INC-TEST-001",
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
    )


def test_retriever_returns_relevant_evidence() -> None:
    retriever = EvidenceRetriever()

    results = retriever.retrieve(make_incident())

    assert results
    assert results[0].record.evidence_id == "EV-001"
    assert results[0].score > 0


def test_retriever_respects_limit() -> None:
    retriever = EvidenceRetriever()

    results = retriever.retrieve(
        make_incident(),
        limit=1,
    )

    assert len(results) == 1


def test_retriever_rejects_invalid_limit() -> None:
    retriever = EvidenceRetriever()

    try:
        retriever.retrieve(make_incident(), limit=0)
    except ValueError as exc:
        assert "at least 1" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_format_results() -> None:
    retriever = EvidenceRetriever()
    results = retriever.retrieve(make_incident())

    formatted = retriever.format_results(results)

    assert "[EV-001]" in formatted
    assert "NVLink" in formatted


def test_format_empty_results() -> None:
    formatted = EvidenceRetriever.format_results([])

    assert formatted == "No retrieved evidence is available."
