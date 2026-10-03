from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from shield.governance.decision import DecisionStatus, DiagnosticDecision


class ActionStatus(StrEnum):
    """Outcome of a repair execution request."""

    EXECUTED = "executed"
    BLOCKED = "blocked"
    REQUIRES_REVIEW = "requires_review"


class ActionResult(BaseModel):
    """Validated result of a repair execution request."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    status: ActionStatus
    action: str = Field(min_length=1)
    message: str = Field(min_length=1)


class RepairExecutor:
    """Controlled boundary for executing approved diagnostic actions."""

    def execute(
        self,
        decision: DiagnosticDecision,
    ) -> ActionResult:
        """Execute or safely block a diagnostic recommendation."""

        if decision.status == DecisionStatus.REJECT:
            return ActionResult(
                incident_id=decision.incident_id,
                status=ActionStatus.BLOCKED,
                action=decision.recommended_action,
                message="Repair blocked by governance decision.",
            )

        if decision.status == DecisionStatus.REVIEW:
            return ActionResult(
                incident_id=decision.incident_id,
                status=ActionStatus.REQUIRES_REVIEW,
                action=decision.recommended_action,
                message="Repair requires human review before execution.",
            )

        return ActionResult(
            incident_id=decision.incident_id,
            status=ActionStatus.EXECUTED,
            action=decision.recommended_action,
            message="Repair action approved for execution.",
        )