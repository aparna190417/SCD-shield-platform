from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceRecord:
    """A verified piece of diagnostic evidence."""

    evidence_id: str
    incident_type: str
    node_id: str
    text: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievedEvidence:
    """Evidence returned by the retrieval layer."""

    record: EvidenceRecord
    score: float
