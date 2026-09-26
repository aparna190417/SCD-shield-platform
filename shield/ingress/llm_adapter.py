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
        """Return the configured response and record the request."""

        self.requests.append(request)
        return self.response