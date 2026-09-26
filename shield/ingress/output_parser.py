import json
from typing import Any

from pydantic import ValidationError

from shield.ingress.schemas import DiagnosticResult


class DiagnosticOutputParser:
    """Parse and validate structured diagnostic output."""

    def parse(self, raw_output: str) -> DiagnosticResult:
        """Parse JSON text and validate the diagnostic result."""

        try:
            payload: Any = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Diagnostic output is not valid JSON."
            ) from exc

        try:
            return DiagnosticResult.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(
                "Diagnostic output failed schema validation."
            ) from exc