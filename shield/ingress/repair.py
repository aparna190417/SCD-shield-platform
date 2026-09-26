from collections.abc import Callable
from dataclasses import dataclass

from shield.ingress.output_parser import DiagnosticOutputParser
from shield.ingress.schemas import DiagnosticResult


@dataclass(frozen=True)
class RepairResult:
    """Result of a diagnostic output repair attempt."""

    result: DiagnosticResult
    attempts: int


class DiagnosticRepairEngine:
    """Repair malformed diagnostic output with bounded retries."""

    def __init__(
        self,
        parser: DiagnosticOutputParser | None = None,
        max_attempts: int = 2,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        self.parser = parser or DiagnosticOutputParser()
        self.max_attempts = max_attempts

    def parse_with_repair(
        self,
        raw_output: str,
        repair_fn: Callable[[str], str],
    ) -> RepairResult:
        """
        Parse diagnostic output and request a repaired response when needed.

        The retry count is bounded by max_attempts.
        """

        current_output = raw_output

        for attempt in range(1, self.max_attempts + 1):
            try:
                result = self.parser.parse(current_output)

                return RepairResult(
                    result=result,
                    attempts=attempt,
                )

            except ValueError:
                if attempt == self.max_attempts:
                    raise

                current_output = repair_fn(current_output)

        raise RuntimeError("Repair loop terminated unexpectedly.")
