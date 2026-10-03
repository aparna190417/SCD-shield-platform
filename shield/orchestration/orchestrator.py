from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict

from shield.engines.repair_executor import ActionResult, RepairExecutor
from shield.governance.decision import DecisionEngine, DiagnosticDecision
from shield.ingress.diagnostic_service import DiagnosticService
from shield.ingress.schemas import DiagnosticResult, Incident


class DiagnosticWorkflowResult(BaseModel):
    """Complete diagnostic, governance, and repair workflow result."""

    model_config = ConfigDict(extra="forbid")

    diagnostic: DiagnosticResult
    decision: DiagnosticDecision
    action: ActionResult

class DiagnosticOrchestrator:
    """Coordinate the end-to-end incident diagnostic workflow."""

    def __init__(
        self,
        diagnostic_service: DiagnosticService,
        *,
        decision_engine: DecisionEngine | None = None,
        repair_executor: RepairExecutor | None = None,
        context_builder: Callable[[Incident], dict[str, Any]] | None = None,
    ) -> None:
        self.diagnostic_service = diagnostic_service
        self.decision_engine = decision_engine or DecisionEngine()
        self.repair_executor = repair_executor or RepairExecutor()
        self.context_builder = context_builder

    def diagnose(
        self,
        incident: Incident,
        *,
        prompt_version: str = "v1",
        hardware_context: str = "",
        retrieved_evidence: str | None = None,
        incident_history: str = "",
    ) -> DiagnosticResult:
        """Run the diagnostic stage only."""

        context: dict[str, Any] = {}

        if self.context_builder is not None:
            context = self.context_builder(incident)

        hardware_context = context.get(
            "hardware_context",
            hardware_context,
        )
        retrieved_evidence = context.get(
            "retrieved_evidence",
            retrieved_evidence,
        )
        incident_history = context.get(
            "incident_history",
            incident_history,
        )

        return self.diagnostic_service.diagnose(
            incident,
            prompt_version=prompt_version,
            hardware_context=hardware_context,
            retrieved_evidence=retrieved_evidence,
            incident_history=incident_history,
        )

    def run(
        self,
        incident: Incident,
        *,
        prompt_version: str = "v1",
        hardware_context: str = "",
        retrieved_evidence: str | None = None,
        incident_history: str = "",
    ) -> DiagnosticWorkflowResult:
        """Run diagnosis, governance evaluation, and repair execution."""

        diagnostic = self.diagnose(
            incident,
            prompt_version=prompt_version,
            hardware_context=hardware_context,
            retrieved_evidence=retrieved_evidence,
            incident_history=incident_history,
        )

        decision = self.decision_engine.evaluate(
            incident,
            diagnostic,
        )

        action = self.repair_executor.execute(decision)

        return DiagnosticWorkflowResult(
            diagnostic=diagnostic,
            decision=decision,
            action=action,
        )