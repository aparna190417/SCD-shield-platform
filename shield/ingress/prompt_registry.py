from pathlib import Path


class PromptRegistry:
    """Load versioned SCD-SHIELD diagnostic prompts."""

    def __init__(self, prompts_root: Path | None = None) -> None:
        if prompts_root is None:
            prompts_root = (
                Path(__file__).resolve().parents[2] / "prompts"
            )

        self.prompts_root = prompts_root

    def load_diagnostic_prompt(self, version: str) -> str:
        """Load a diagnostic system prompt by version."""

        if not version:
            raise ValueError("Prompt version must not be empty.")

        prompt_path = (
            self.prompts_root
            / version
            / "diagnostic_system.md"
        )

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Diagnostic prompt not found for version: {version}"
            )

        return prompt_path.read_text(encoding="utf-8")