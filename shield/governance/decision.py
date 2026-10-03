from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from shield.ingress.schemas import DiagnosticResult, Incident


class DecisionStatus(StrEnum):
    """Governance decision for a diagnostic recommendation."""

    APPROVE = "approve"
    REVIEW = "review"
    REJECT = "reject"


class DiagnosticDecision(BaseModel):
    """Validated governance decision for a diagnostic result."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    status: DecisionStatus
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)


class DecisionEngine:
    """Apply deterministic safety rules to diagnostic recommendations."""

    def __init__(
        self,
        *,
        approval_threshold: float = 0.80,
        review_threshold: float = 0.60,
    ) -> None:
        if not 0.0 <= review_threshold <= 1.0:
            raise ValueError("review_threshold must be between 0 and 1.")

        if not 0.0 <= approval_threshold <= 1.0:
            raise ValueError("approval_threshold must be between 0 and 1.")

        if review_threshold > approval_threshold:
            raise ValueError(
                "review_threshold cannot exceed approval_threshold."
            )

        self.approval_threshold = approval_threshold
        self.review_threshold = review_threshold

    def evaluate(
        self,
        incident: Incident,
        diagnostic: DiagnosticResult,
    ) -> DiagnosticDecision:
        """Evaluate whether a diagnostic recommendation may proceed."""

        if diagnostic.incident_id != incident.incident_id:
            return DiagnosticDecision(
                incident_id=incident.incident_id,
                status=DecisionStatus.REJECT,
                confidence=diagnostic.confidence,
                reason="Diagnostic incident ID does not match the incident.",
                recommended_action=diagnostic.recommended_action,
            )

        if not diagnostic.recommended_action.strip():
            return DiagnosticDecision(
                incident_id=incident.incident_id,
                status=DecisionStatus.REJECT,
                confidence=diagnostic.confidence,
                reason="No actionable recommendation was provided.",
                recommended_action=diagnostic.recommended_action,
            )

        if diagnostic.confidence >= self.approval_threshold:
            status = DecisionStatus.APPROVE
            reason = "Diagnostic confidence meets the approval threshold."
        elif diagnostic.confidence >= self.review_threshold:
            status = DecisionStatus.REVIEW
            reason = "Diagnostic confidence requires human review."
        else:
            status = DecisionStatus.REJECT
            reason = "Diagnostic confidence is below the review threshold."

        return DiagnosticDecision(
            incident_id=incident.incident_id,
            status=status,
            confidence=diagnostic.confidence,
            reason=reason,
            recommended_action=diagnostic.recommended_action,
        )