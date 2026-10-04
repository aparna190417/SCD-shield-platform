import re
from dataclasses import dataclass
from typing import Protocol

from shield.ingress.prompt_registry import PromptBundle


@dataclass(frozen=True)
class LLMRequest:
    """Structured request sent to an LLM provider."""

    prompt: PromptBundle


class LLMAdapter(Protocol):
    """Interface implemented by concrete LLM providers."""

    def generate(self, request: LLMRequest) -> str:
        """Generate a raw model response."""
        ...


class FakeLLMAdapter:
    """Deterministic LLM adapter for development and testing."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> str:
        """Return a deterministic response matching the incident ID."""

        self.requests.append(request)

        incident_id = self._extract_incident_id(request)

        if incident_id is None:
            return self.response

        return self.response.replace(
            '"incident_id": "INC-001"',
            f'"incident_id": "{incident_id}"',
            1,
        )

    @staticmethod
    def _extract_incident_id(request: LLMRequest) -> str | None:
        """Extract incident ID from the rendered user prompt."""

        match = re.search(
            r'"incident_id"\s*:\s*"([^"]+)"',
            request.prompt.user,
        )

        if match:
            return match.group(1)

        return None
