from shield.ingress.llm_adapter import (
    FakeLLMAdapter,
    LLMRequest,
)
from shield.ingress.prompt_registry import PromptBundle


def test_fake_llm_adapter_returns_response():
    bundle = PromptBundle(
        system="system instructions",
        developer="developer instructions",
        user="incident: INC-001",
    )

    adapter = FakeLLMAdapter('{"status": "ok"}')

    response = adapter.generate(
        LLMRequest(prompt=bundle)
    )

    assert response == '{"status": "ok"}'


def test_fake_llm_adapter_records_request():
    bundle = PromptBundle(
        system="system instructions",
        developer="developer instructions",
        user="incident: INC-002",
    )

    adapter = FakeLLMAdapter("response")

    request = LLMRequest(prompt=bundle)

    adapter.generate(request)

    assert len(adapter.requests) == 1
    assert adapter.requests[0] == request