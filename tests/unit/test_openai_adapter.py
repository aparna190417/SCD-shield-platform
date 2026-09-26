from types import SimpleNamespace

import pytest

from shield.ingress.llm_adapter import LLMRequest
from shield.ingress.openai_adapter import OpenAIAdapter
from shield.ingress.prompt_renderer import RenderedPromptBundle


class FakeCompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs

        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeChat:
    def __init__(self, content: str) -> None:
        self.completions = FakeCompletions(content)


class FakeOpenAIClient:
    def __init__(self, content: str) -> None:
        self.chat = FakeChat(content)


def make_request() -> LLMRequest:
    prompt = RenderedPromptBundle(
        system="System prompt",
        developer="Developer prompt",
        user="User prompt",
    )

    return LLMRequest(prompt=prompt)


def test_openai_adapter_returns_response() -> None:
    client = FakeOpenAIClient('{"status": "ok"}')

    adapter = OpenAIAdapter(
        api_key="test-key",
        model="test-model",
        client=client,
    )

    result = adapter.generate(make_request())

    assert result == '{"status": "ok"}'


def test_openai_adapter_sends_all_prompt_layers() -> None:
    client = FakeOpenAIClient('{"status": "ok"}')

    adapter = OpenAIAdapter(
        api_key="test-key",
        model="test-model",
        client=client,
    )

    adapter.generate(make_request())

    request = client.chat.completions.last_kwargs

    assert request["model"] == "test-model"
    assert request["messages"] == [
        {
            "role": "system",
            "content": "System prompt",
        },
        {
            "role": "developer",
            "content": "Developer prompt",
        },
        {
            "role": "user",
            "content": "User prompt",
        },
    ]


def test_openai_adapter_rejects_missing_api_key() -> None:
    with pytest.raises(ValueError, match="API key is required"):
        OpenAIAdapter(api_key="")


def test_openai_adapter_rejects_empty_response() -> None:
    client = FakeOpenAIClient("")

    adapter = OpenAIAdapter(
        api_key="test-key",
        client=client,
    )

    with pytest.raises(ValueError, match="empty response"):
        adapter.generate(make_request())
