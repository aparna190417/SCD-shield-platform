from shield.ingress.prompt_registry import PromptRegistry


def test_load_v1_prompt_bundle():
    registry = PromptRegistry()

    bundle = registry.load_prompt_bundle("v1")

    assert "SCD-SHIELD" in bundle.system
    assert "diagnostic procedure" in bundle.developer.lower()
    assert "{incident}" in bundle.user


def test_load_v2_challenger_prompt_bundle():
    registry = PromptRegistry()

    bundle = registry.load_prompt_bundle("v2_challenger")

    assert "challenger" in bundle.system.lower()
    assert "competing hypotheses" in bundle.developer.lower()
    assert "{telemetry}" in bundle.user


def test_prompt_bundle_contains_three_layers():
    registry = PromptRegistry()

    bundle = registry.load_prompt_bundle("v1")

    assert bundle.system
    assert bundle.developer
    assert bundle.user
