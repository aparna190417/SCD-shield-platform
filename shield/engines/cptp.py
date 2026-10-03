from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CPTPStatus(StrEnum):
    """Result status produced by the deterministic CPTP engine."""

    SAFE = "safe"
    WARNING = "warning"
    CRITICAL = "critical"
    INVALID = "invalid"


class CPTPInput(BaseModel):
    """Validated thermal and power telemetry for CPTP evaluation."""

    model_config = ConfigDict(extra="forbid")

    temperature_c: int = Field(ge=0, le=200)
    temperature_limit_c: int = Field(ge=1, le=200)

    power_w: int = Field(ge=0)
    power_limit_w: int = Field(ge=1)

    temperature_warning_percent: int = Field(
        default=80,
        ge=1,
        le=100,
    )
    power_warning_percent: int = Field(
        default=80,
        ge=1,
        le=100,
    )


class CPTPResult(BaseModel):
    """Deterministic CPTP evaluation result."""

    model_config = ConfigDict(extra="forbid")

    status: CPTPStatus

    temperature_c: int = Field(ge=0)
    temperature_limit_c: int = Field(ge=1)

    power_w: int = Field(ge=0)
    power_limit_w: int = Field(ge=1)

    temperature_percent: int = Field(ge=0)
    power_percent: int = Field(ge=0)

    temperature_headroom_c: int
    power_headroom_w: int

    reason: str = Field(min_length=1)
    controls: list[str] = Field(default_factory=list)


class CPTPEngine:
    """
    Deterministic Cluster Thermal/Power Protection engine.

    All percentage calculations use integer arithmetic.
    No floating-point arithmetic is used for thermal or power controls.

    Decision order:
        1. Invalid configuration/input -> INVALID
        2. Any hard limit reached/exceeded -> CRITICAL
        3. Any warning threshold reached/exceeded -> WARNING
        4. Otherwise -> SAFE
    """

    def evaluate(self, telemetry: CPTPInput) -> CPTPResult:
        """Evaluate thermal and power safety constraints."""

        if (
            telemetry.temperature_warning_percent
            > 100
            or telemetry.power_warning_percent > 100
        ):
            return self._invalid_result(
                telemetry,
                "Warning threshold cannot exceed 100 percent.",
            )

        temperature_percent = self._percentage(
            telemetry.temperature_c,
            telemetry.temperature_limit_c,
        )

        power_percent = self._percentage(
            telemetry.power_w,
            telemetry.power_limit_w,
        )

        temperature_headroom = (
            telemetry.temperature_limit_c
            - telemetry.temperature_c
        )

        power_headroom = (
            telemetry.power_limit_w
            - telemetry.power_w
        )

        controls: list[str] = []

        temperature_critical = (
            telemetry.temperature_c
            >= telemetry.temperature_limit_c
        )

        power_critical = (
            telemetry.power_w
            >= telemetry.power_limit_w
        )

        temperature_warning = (
            temperature_percent
            >= telemetry.temperature_warning_percent
        )

        power_warning = (
            power_percent
            >= telemetry.power_warning_percent
        )

        if temperature_critical:
            controls.append("thermal_protection")

        if power_critical:
            controls.append("power_protection")

        if temperature_warning and not temperature_critical:
            controls.append("thermal_mitigation")

        if power_warning and not power_critical:
            controls.append("power_mitigation")

        if temperature_critical or power_critical:
            return CPTPResult(
                status=CPTPStatus.CRITICAL,
                temperature_c=telemetry.temperature_c,
                temperature_limit_c=telemetry.temperature_limit_c,
                power_w=telemetry.power_w,
                power_limit_w=telemetry.power_limit_w,
                temperature_percent=temperature_percent,
                power_percent=power_percent,
                temperature_headroom_c=temperature_headroom,
                power_headroom_w=power_headroom,
                reason=self._critical_reason(
                    temperature_critical,
                    power_critical,
                ),
                controls=controls,
            )

        if temperature_warning or power_warning:
            return CPTPResult(
                status=CPTPStatus.WARNING,
                temperature_c=telemetry.temperature_c,
                temperature_limit_c=telemetry.temperature_limit_c,
                power_w=telemetry.power_w,
                power_limit_w=telemetry.power_limit_w,
                temperature_percent=temperature_percent,
                power_percent=power_percent,
                temperature_headroom_c=temperature_headroom,
                power_headroom_w=power_headroom,
                reason=self._warning_reason(
                    temperature_warning,
                    power_warning,
                ),
                controls=controls,
            )

        return CPTPResult(
            status=CPTPStatus.SAFE,
            temperature_c=telemetry.temperature_c,
            temperature_limit_c=telemetry.temperature_limit_c,
            power_w=telemetry.power_w,
            power_limit_w=telemetry.power_limit_w,
            temperature_percent=temperature_percent,
            power_percent=power_percent,
            temperature_headroom_c=temperature_headroom,
            power_headroom_w=power_headroom,
            reason="Thermal and power telemetry are within safe limits.",
            controls=[],
        )

    @staticmethod
    def _percentage(value: int, limit: int) -> int:
        """
        Calculate percentage using integer arithmetic.

        The result is rounded down deliberately so that the safety
        decision is deterministic and reproducible.
        """

        return (value * 100) // limit

    @staticmethod
    def _critical_reason(
        temperature_critical: bool,
        power_critical: bool,
    ) -> str:
        if temperature_critical and power_critical:
            return "Thermal and power hard limits have been reached."

        if temperature_critical:
            return "Thermal hard limit has been reached."

        return "Power hard limit has been reached."

    @staticmethod
    def _warning_reason(
        temperature_warning: bool,
        power_warning: bool,
    ) -> str:
        if temperature_warning and power_warning:
            return "Thermal and power warning thresholds have been reached."

        if temperature_warning:
            return "Thermal warning threshold has been reached."

        return "Power warning threshold has been reached."

    @staticmethod
    def _invalid_result(
        telemetry: CPTPInput,
        reason: str,
    ) -> CPTPResult:
        return CPTPResult(
            status=CPTPStatus.INVALID,
            temperature_c=telemetry.temperature_c,
            temperature_limit_c=telemetry.temperature_limit_c,
            power_w=telemetry.power_w,
            power_limit_w=telemetry.power_limit_w,
            temperature_percent=0,
            power_percent=0,
            temperature_headroom_c=(
                telemetry.temperature_limit_c
                - telemetry.temperature_c
            ),
            power_headroom_w=(
                telemetry.power_limit_w
                - telemetry.power_w
            ),
            reason=reason,
            controls=["configuration_review"],
        )