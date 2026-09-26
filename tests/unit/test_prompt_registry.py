from pathlib import Path

import pytest

from shield.ingress.prompt_registry import PromptRegistry


def test_load_v1_prompt():
    registry = PromptRegistry()

    prompt = registry.load_diagnostic_prompt("v1")

    assert "SCD-SHIELD" in prompt
    assert "Required behavior" in prompt


def test_load_v2_challenger_prompt():
    registry = PromptRegistry()

    prompt = registry.load_diagnostic_prompt("v2_challenger")

    assert "challenger" in prompt.lower()
    assert "three plausible competing hypotheses" in prompt


def test_missing_prompt_version():
    registry = PromptRegistry()

    with pytest.raises(FileNotFoundError):
        registry.load_diagnostic_prompt("v999")


def test_empty_prompt_version():
    registry = PromptRegistry()

    with pytest.raises(ValueError):
        registry.load_diagnostic_prompt("")