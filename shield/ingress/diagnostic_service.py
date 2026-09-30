import logging

from shield.ingress.llm_adapter import LLMAdapter, LLMRequest
from shield.ingress.prompt_registry import PromptRegistry
from shield.ingress.prompt_renderer import PromptRenderer, RenderedPromptBundle
from shield.ingress.repair import DiagnosticRepairEngine
from shield.ingress.schemas import DiagnosticResult, Incident
from shield.retrieval.retriever import EvidenceRetriever

logger = logging.getLogger(__name__)


class DiagnosticService:
    """End-to-end diagnostic ingress service."""

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        prompt_registry: PromptRegistry | None = None,
        prompt_renderer: PromptRenderer | None = None,
        repair_engine: DiagnosticRepairEngine | None = None,
        evidence_retriever: EvidenceRetriever | None = None,
    ) -> None:
        self.llm_adapter = llm_adapter
        self.prompt_registry = prompt_registry or PromptRegistry()
        self.prompt_renderer = prompt_renderer or PromptRenderer()
        self.repair_engine = repair_engine or DiagnosticRepairEngine()
        self.evidence_retriever = evidence_retriever or EvidenceRetriever()

    def diagnose(
        self,
        incident: Incident,
        *,
        prompt_version: str = "v1",
        hardware_context: str = "",
        retrieved_evidence: str | None = None,
        incident_history: str = "",
    ) -> DiagnosticResult:
        """Run the complete diagnostic pipeline."""

        logger.info(
            "Starting diagnostic",
            extra={
                "incident_id": incident.incident_id,
                "prompt_version": prompt_version,
            },
        )

        bundle = self.prompt_registry.load_prompt_bundle(prompt_version)

        if retrieved_evidence is None:
            logger.debug(
                "Retrieving evidence",
                extra={
                    "incident_id": incident.incident_id,
                },
            )

            retrieved_results = self.evidence_retriever.retrieve(incident)

            retrieved_evidence = self.evidence_retriever.format_results(
                retrieved_results
            )

            logger.info(
                "Evidence retrieval completed",
                extra={
                    "incident_id": incident.incident_id,
                    "evidence_count": len(retrieved_results),
                },
            )
        else:
            logger.debug(
                "Using provided retrieved evidence",
                extra={
                    "incident_id": incident.incident_id,
                },
            )

        rendered = self.prompt_renderer.render(
            bundle,
            incident=incident.model_dump_json(),
            telemetry=str(incident.telemetry),
            hardware_context=hardware_context,
            retrieved_evidence=retrieved_evidence,
            incident_history=incident_history,
        )

        request = LLMRequest(prompt=rendered)

        logger.info(
            "Sending initial diagnostic request",
            extra={
                "incident_id": incident.incident_id,
            },
        )

        initial_output = self.llm_adapter.generate(request)

        logger.debug(
            "Initial diagnostic response received",
            extra={
                "incident_id": incident.incident_id,
                "response_length": len(initial_output),
            },
        )

        repair_used = False

        def repair_output(_: str) -> str:
            nonlocal repair_used

            repair_used = True

            logger.warning(
                "Repairing diagnostic response",
                extra={
                    "incident_id": incident.incident_id,
                },
            )

            repair_request = LLMRequest(
                prompt=RenderedPromptBundle(
                    system=rendered.system,
                    developer=(
                        rendered.developer
                        + "\n\nRepair the previous output and return "
                        "only valid structured JSON."
                    ),
                    user=rendered.user,
                )
            )

            repaired_output = self.llm_adapter.generate(repair_request)

            logger.debug(
                "Repair response received",
                extra={
                    "incident_id": incident.incident_id,
                    "response_length": len(repaired_output),
                },
            )

            return repaired_output

        repaired = self.repair_engine.parse_with_repair(
            initial_output,
            repair_output,
        )

        logger.info(
            "Diagnostic completed",
            extra={
                "incident_id": incident.incident_id,
                "repair_used": repair_used,
            },
        )

        return repaired.result