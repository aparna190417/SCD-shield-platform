import httpx
import pytest

from shield.ingress.llm_adapter import LLMRequest
from shield.ingress.openai_adapter import OpenAIAdapter
from shield.ingress.prompt_renderer import RenderedPromptBundle


def make_request() -> LLMRequest:
    return LLMRequest(
        prompt=RenderedPromptBundle(
            system="You are a diagnostic system.",
            developer="Return structured JSON.",
            user="Analyze this incident.",
        )
    )


class FakeMessage:
    def __init__(self, content: str | None):
        self.content = content


class FakeChoice:
    def __init__(self, content: str | None):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content: str | None):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.received_kwargs = None

    def create(self, **kwargs):
        self.received_kwargs = kwargs
        return self.response


class FakeChat:
    def __init__(self, completions: FakeCompletions):
        self.completions = completions


class FakeClient:
    def __init__(self, response: FakeResponse):
        self.completions = FakeCompletions(response)
        self.chat = FakeChat(self.completions)


def test_openai_adapter_requires_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="OpenAI API key is required",
    ):
        OpenAIAdapter(api_key="")


def test_openai_adapter_uses_provided_client() -> None:
    client = FakeClient(FakeResponse("test response"))

    adapter = OpenAIAdapter(
        api_key="test-key",
        client=client,
    )

    assert adapter.client is client
    assert adapter.model == "gpt-4o-mini"


def test_openai_adapter_generates_response() -> None:
    client = FakeClient(FakeResponse("diagnostic response"))

    adapter = OpenAIAdapter(
        api_key="test-key",
        client=client,
    )

    result = adapter.generate(make_request())

    assert result == "diagnostic response"


def test_openai_adapter_sends_correct_messages() -> None:
    client = FakeClient(FakeResponse("diagnostic response"))

    adapter = OpenAIAdapter(
        api_key="test-key",
        model="test-model",
        client=client,
    )

    adapter.generate(make_request())

    kwargs = client.completions.received_kwargs

    assert kwargs is not None
    assert kwargs["model"] == "test-model"
    assert kwargs["messages"] == [
        {
            "role": "system",
            "content": "You are a diagnostic system.",
        },
        {
            "role": "developer",
            "content": "Return structured JSON.",
        },
        {
            "role": "user",
            "content": "Analyze this incident.",
        },
    ]


def test_openai_adapter_rejects_empty_response() -> None:
    client = FakeClient(FakeResponse(None))

    adapter = OpenAIAdapter(
        api_key="test-key",
        client=client,
    )

    with pytest.raises(
        ValueError,
        match="LLM returned an empty response",
    ):
        adapter.generate(make_request())


def test_openai_adapter_handles_rate_limit_error() -> None:
    from openai import RateLimitError

    class RateLimitCompletions:
        def create(self, **kwargs):
            response = httpx.Response(
                429,
                request=httpx.Request(
                    "POST",
                    "https://api.openai.com/v1/chat/completions",
                ),
            )

            raise RateLimitError(
                "Quota exceeded",
                response=response,
                body=None,
            )

    class RateLimitChat:
        completions = RateLimitCompletions()

    class RateLimitClient:
        chat = RateLimitChat()

    adapter = OpenAIAdapter(
        api_key="test-key",
        client=RateLimitClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="rate limit or quota exceeded",
    ):
        adapter.generate(make_request())


def test_openai_adapter_handles_api_status_error() -> None:
    from openai import APIStatusError

    class StatusCompletions:
        def create(self, **kwargs):
            response = httpx.Response(
                500,
                request=httpx.Request(
                    "POST",
                    "https://api.openai.com/v1/chat/completions",
                ),
            )

            raise APIStatusError(
                "API request failed",
                response=response,
                body=None,
            )

    class StatusChat:
        completions = StatusCompletions()

    class StatusClient:
        chat = StatusChat()

    adapter = OpenAIAdapter(
        api_key="test-key",
        client=StatusClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="OpenAI API request failed",
    ):
        adapter.generate(make_request())