from shield.ingress.schemas import Incident
from shield.retrieval.models import RetrievedEvidence
from shield.retrieval.store import LocalEvidenceStore


class EvidenceRetriever:
    """Deterministic keyword-based evidence retriever."""

    def __init__(
        self,
        store: LocalEvidenceStore | None = None,
    ) -> None:
        self.store = store or LocalEvidenceStore()

    def retrieve(
        self,
        incident: Incident,
        *,
        limit: int = 3,
    ) -> list[RetrievedEvidence]:
        """Retrieve evidence relevant to the supplied incident."""

        if limit < 1:
            raise ValueError("limit must be at least 1.")

        query_terms = self._query_terms(incident)

        results: list[RetrievedEvidence] = []

        for record in self.store.all_records():
            score = self._score(record, query_terms)

            if score > 0:
                results.append(
                    RetrievedEvidence(
                        record=record,
                        score=score,
                    )
                )

        results.sort(
            key=lambda item: (-item.score, item.record.evidence_id)
        )

        return results[:limit]

    @staticmethod
    def _query_terms(incident: Incident) -> set[str]:
        """Build normalized retrieval terms from the incident."""

        terms = {
            incident.incident_type.lower(),
            incident.node_id.lower(),
            incident.description.lower(),
        }

        terms.update(
            str(key).lower()
            for key in incident.telemetry
        )

        return {
            term
            for value in terms
            for term in value.replace("_", " ").split()
            if term
        }

    @staticmethod
    def _score(
        record: object,
        query_terms: set[str],
    ) -> float:
        """Calculate a simple deterministic relevance score."""

        searchable = " ".join(
            [
                record.incident_type,
                record.node_id,
                record.text,
                *record.tags,
            ]
        ).lower()

        matched_terms = {
            term
            for term in query_terms
            if term in searchable
        }

        return float(len(matched_terms))

    @staticmethod
    def format_results(
        results: list[RetrievedEvidence],
    ) -> str:
        """Format retrieved evidence for prompt injection."""

        if not results:
            return "No retrieved evidence is available."

        lines = []

        for item in results:
            lines.append(
                f"[{item.record.evidence_id}] "
                f"{item.record.text}"
            )

        return "\n".join(lines)
