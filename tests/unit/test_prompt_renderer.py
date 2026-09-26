from shield.ingress.prompt_registry import PromptRegistry
from shield.ingress.prompt_renderer import PromptRenderer


def test_render_injects_all_runtime_variables():
    registry = PromptRegistry()
    bundle = registry.load_prompt_bundle("v1")

    renderer = PromptRenderer()

    rendered = renderer.render(
        bundle,
        incident="INC-001: NVLink degradation detected",
        telemetry="link_errors=42",
        hardware_context="GPU-A100 node-a",
        retrieved_evidence="NVLink documentation indicates link errors can indicate degradation",
        incident_history="Previous similar incident occurred on node-b",
    )

    assert "INC-001: NVLink degradation detected" in rendered.user
    assert "link_errors=42" in rendered.user
    assert "GPU-A100 node-a" in rendered.user
    assert "NVLink documentation" in rendered.user
    assert "Previous similar incident" in rendered.user


def test_render_preserves_system_and_developer_prompts():
    registry = PromptRegistry()
    bundle = registry.load_prompt_bundle("v1")

    renderer = PromptRenderer()

    rendered = renderer.render(
        bundle,
        incident="INC-002",
        telemetry="temperature=82C",
        hardware_context="GPU node-c",
        retrieved_evidence="No additional evidence",
        incident_history="No matching incidents",
    )

    assert rendered.system == bundle.system
    assert rendered.developer == bundle.developer