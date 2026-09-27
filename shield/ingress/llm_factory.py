from shield.config.settings import Settings
from shield.ingress.llm_adapter import FakeLLMAdapter, LLMAdapter
from shield.ingress.openai_adapter import OpenAIAdapter

FAKE_DIAGNOSTIC_OUTPUT = """
{
    "incident_id": "INC-001",
    "failure_family": "interconnect",
    "affected_entity": "node-a",
    "primary_hypothesis": "NVLink degradation",
    "alternative_hypotheses": [
        "Transient communication fault"
    ],
    "supporting_evidence": [
        "link_errors=42"
    ],
    "contradicting_evidence": [],
    "missing_evidence": [
        "NVLink health counters"
    ],
    "confidence": 0.82,
    "recommended_action": "Collect NVLink health counters"
}
"""


def create_llm_adapter(settings: Settings) -> LLMAdapter:
    """Create the configured LLM provider."""

    provider = settings.llm_provider.strip().lower()

    if provider == "fake":
        return FakeLLMAdapter(response=FAKE_DIAGNOSTIC_OUTPUT)

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        return OpenAIAdapter(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
