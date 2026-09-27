from shield.retrieval.models import EvidenceRecord


class LocalEvidenceStore:
    """Small deterministic evidence store for development and testing."""

    def __init__(
        self,
        records: list[EvidenceRecord] | None = None,
    ) -> None:
        self.records = records or [
            EvidenceRecord(
                evidence_id="EV-001",
                incident_type="hardware",
                node_id="node-a",
                text=(
                    "Previous NVLink incidents on node-a showed "
                    "increased link errors before communication degradation."
                ),
                tags=("nvlink", "link_errors", "interconnect"),
            ),
            EvidenceRecord(
                evidence_id="EV-002",
                incident_type="hardware",
                node_id="node-b",
                text=(
                    "NVLink health counters were collected during a "
                    "previous interconnect investigation."
                ),
                tags=("nvlink", "health_counters", "interconnect"),
            ),
            EvidenceRecord(
                evidence_id="EV-003",
                incident_type="network",
                node_id="node-c",
                text=(
                    "Transient network communication faults can produce "
                    "short-lived communication errors."
                ),
                tags=("network", "communication"),
            ),
        ]

    def all_records(self) -> list[EvidenceRecord]:
        """Return all available evidence records."""

        return list(self.records)
