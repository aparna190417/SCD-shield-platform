import pytest

from shield.config.settings import Settings
from shield.ingress.llm_adapter import FakeLLMAdapter
from shield.ingress.llm_factory import create_llm_adapter
from shield.ingress.openai_adapter import OpenAIAdapter


def test_factory_creates_fake_adapter() -> None:
    settings = Settings(llm_provider="fake")

    adapter = create_llm_adapter(settings)

    assert isinstance(adapter, FakeLLMAdapter)


def test_factory_rejects_openai_without_api_key() -> None:
    settings = Settings(
        llm_provider="openai",
        openai_api_key=None,
    )

    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        create_llm_adapter(settings)


def test_factory_rejects_unknown_provider() -> None:
    settings = Settings(llm_provider="unknown")

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm_adapter(settings)


def test_factory_creates_openai_adapter() -> None:
    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        openai_model="test-model",
    )

    adapter = create_llm_adapter(settings)

    assert isinstance(adapter, OpenAIAdapter)
    assert adapter.model == "test-model"
