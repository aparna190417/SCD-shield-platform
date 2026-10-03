from shield.ingress.schemas import Incident
from shield.retrieval.retriever import EvidenceRetriever


class IncidentContextBuilder:
    """Build diagnostic context from incident data and retrieved evidence."""

    def __init__(
        self,
        retriever: EvidenceRetriever | None = None,
        *,
        retrieval_limit: int = 3,
    ) -> None:
        if retrieval_limit < 1:
            raise ValueError("retrieval_limit must be at least 1.")

        self.retriever = retriever or EvidenceRetriever()
        self.retrieval_limit = retrieval_limit

    def build(self, incident: Incident) -> dict[str, str]:
        """Build prompt-ready context for an incident."""

        results = self.retriever.retrieve(
            incident,
            limit=self.retrieval_limit,
        )

        retrieved_evidence = self.retriever.format_results(results)

        hardware_context = (
            f"Node: {incident.node_id}\n"
            f"Incident type: {incident.incident_type}\n"
            f"Severity: {incident.severity}\n"
            f"Description: {incident.description}"
        )

        incident_history = (
            f"Current incident: {incident.incident_id}\n"
            f"Timestamp: {incident.timestamp.isoformat()}"
        )

        return {
            "hardware_context": hardware_context,
            "retrieved_evidence": retrieved_evidence,
            "incident_history": incident_history,
        }