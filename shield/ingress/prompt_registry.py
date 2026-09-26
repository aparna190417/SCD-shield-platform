from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptBundle:
    """Three-tier prompt messages for a diagnostic request."""

    system: str
    developer: str
    user: str


class PromptRegistry:
    """Load versioned three-tier SCD-SHIELD prompts."""

    def __init__(self, prompts_root: Path | None = None) -> None:
        if prompts_root is None:
            prompts_root = Path(__file__).resolve().parents[2] / "prompts"

        self.prompts_root = prompts_root

    def load_diagnostic_prompt(self, version: str) -> str:
        """Backward-compatible loading of the legacy diagnostic prompt."""

        prompt_path = self.prompts_root / version / "diagnostic_system.md"

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Diagnostic prompt not found for version: {version}"
            )

        return prompt_path.read_text(encoding="utf-8")

    def load_prompt_bundle(self, version: str) -> PromptBundle:
        """Load system, developer, and user prompt layers."""

        version_dir = self.prompts_root / version

        if not version_dir.exists():
            raise FileNotFoundError(f"Prompt version not found: {version}")

        messages = {}

        for layer in ("system", "developer", "user"):
            path = version_dir / f"{layer}.md"

            if not path.exists():
                raise FileNotFoundError(
                    f"Missing {layer} prompt for version: {version}"
                )

            messages[layer] = path.read_text(encoding="utf-8")

        return PromptBundle(**messages)
