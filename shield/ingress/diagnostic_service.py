from shield.ingress.llm_adapter import LLMAdapter, LLMRequest
from shield.ingress.prompt_registry import PromptRegistry
from shield.ingress.prompt_renderer import PromptRenderer, RenderedPromptBundle
from shield.ingress.repair import DiagnosticRepairEngine
from shield.ingress.schemas import DiagnosticResult, Incident
from shield.retrieval.retriever import EvidenceRetriever


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

        bundle = self.prompt_registry.load_prompt_bundle(prompt_version)

        if retrieved_evidence is None:
            retrieved_results = self.evidence_retriever.retrieve(incident)
            retrieved_evidence = self.evidence_retriever.format_results(
                retrieved_results
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

        initial_output = self.llm_adapter.generate(request)

        def repair_output(_: str) -> str:
            repair_request = LLMRequest(
                prompt=RenderedPromptBundle(
                    system=rendered.system,
                    developer=(
                        rendered.developer
                        + "\n\nRepair the previous output and return "
                        "only valid structured JSON."
                    ),
                    user=rendered.user,))

            return self.llm_adapter.generate(repair_request)

        repaired = self.repair_engine.parse_with_repair(
            initial_output,
            repair_output,)

        return repaired.result
