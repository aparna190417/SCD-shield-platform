from enum import StrEnum
from typing import Any

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
            return self._decision(
                incident=incident,
                diagnostic=diagnostic,
                status=DecisionStatus.REJECT,
                reason="Diagnostic incident ID does not match the incident.",
            )

        if not diagnostic.recommended_action.strip():
            return self._decision(
                incident=incident,
                diagnostic=diagnostic,
                status=DecisionStatus.REJECT,
                reason="No actionable recommendation was provided.",
            )

        cptp_status = self._cptp_status(incident)

        # Critical incidents are always fail-safe.
        if incident.severity == "critical":
            if cptp_status == "critical":
                reason = (
                    "Critical CPTP condition detected. "
                    "Repair is rejected by fail-safe governance."
                )
            elif cptp_status == "warning":
                reason = (
                    "Critical incident with CPTP warning condition detected. "
                    "Repair is rejected by fail-safe governance."
                )
            else:
                reason = (
                    "Critical incident requires CPTP-aware fail-safe "
                    "governance and cannot be automatically approved."
                )

            return self._decision(
                incident=incident,
                diagnostic=diagnostic,
                status=DecisionStatus.REJECT,
                reason=reason,
            )

        # High-severity CPTP warnings always require human review.
        if incident.severity == "high" and cptp_status == "warning":
            return self._decision(
                incident=incident,
                diagnostic=diagnostic,
                status=DecisionStatus.REVIEW,
                reason=(
                    "High-severity CPTP warning requires human review "
                    "before repair execution."
                ),
            )

        # Standard confidence-based governance.
        if diagnostic.confidence >= self.approval_threshold:
            status = DecisionStatus.APPROVE
            reason = "Diagnostic confidence meets the approval threshold."
        elif diagnostic.confidence >= self.review_threshold:
            status = DecisionStatus.REVIEW
            reason = "Diagnostic confidence requires human review."
        else:
            status = DecisionStatus.REJECT
            reason = "Diagnostic confidence is below the review threshold."

        return self._decision(
            incident=incident,
            diagnostic=diagnostic,
            status=status,
            reason=reason,
        )

    @staticmethod
    def _decision(
        *,
        incident: Incident,
        diagnostic: DiagnosticResult,
        status: DecisionStatus,
        reason: str,
    ) -> DiagnosticDecision:
        """Build a validated governance decision."""

        return DiagnosticDecision(
            incident_id=incident.incident_id,
            status=status,
            confidence=diagnostic.confidence,
            reason=reason,
            recommended_action=diagnostic.recommended_action,
        )

    @staticmethod
    def _cptp_status(incident: Incident) -> str | None:
        """Classify thermal and power telemetry for governance."""

        telemetry: dict[str, Any] = incident.telemetry

        temperature = DecisionEngine._number(
            telemetry,
            "temperature",
            "temperature_c",
        )
        temperature_limit = DecisionEngine._number(
            telemetry,
            "temperature_limit",
            "temperature_limit_c",
        )

        power = DecisionEngine._number(
            telemetry,
            "power_w",
        )
        power_limit = DecisionEngine._number(
            telemetry,
            "power_limit_w",
        )

        critical = False
        warning = False

        if (
            temperature is not None
            and temperature_limit is not None
            and temperature_limit > 0
        ):
            temperature_percent = (
                temperature / temperature_limit
            ) * 100

            if temperature_percent >= 100:
                critical = True
            elif temperature_percent >= 80:
                warning = True

        if (
            power is not None
            and power_limit is not None
            and power_limit > 0
        ):
            power_percent = (power / power_limit) * 100

            if power_percent >= 100:
                critical = True
            elif power_percent >= 80:
                warning = True

        if critical:
            return "critical"

        if warning:
            return "warning"

        return None

    @staticmethod
    def _number(
        telemetry: dict[str, Any],
        *keys: str,
    ) -> float | None:
        """Read the first numeric telemetry value."""

        for key in keys:
            value = telemetry.get(key)

            if isinstance(value, bool):
                continue

            if isinstance(value, (int, float)):
                return float(value)

        return None