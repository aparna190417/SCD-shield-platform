from dataclasses import dataclass

from shield.ingress.prompt_registry import PromptBundle


@dataclass(frozen=True)
class RenderedPromptBundle:
    """Prompt messages after runtime variable injection."""

    system: str
    developer: str
    user: str


class PromptRenderer:
    """Render a prompt bundle using runtime diagnostic context."""

    REQUIRED_VARIABLES = (
        "incident",
        "telemetry",
        "hardware_context",
        "retrieved_evidence",
        "incident_history",
    )

    def render(
        self,
        bundle: PromptBundle,
        *,
        incident: str,
        telemetry: str,
        hardware_context: str,
        retrieved_evidence: str,
        incident_history: str,
    ) -> RenderedPromptBundle:
        variables = {
            "incident": incident,
            "telemetry": telemetry,
            "hardware_context": hardware_context,
            "retrieved_evidence": retrieved_evidence,
            "incident_history": incident_history,
        }

        return RenderedPromptBundle(
            system=bundle.system,
            developer=bundle.developer,
            user=bundle.user.format(**variables),
        )
