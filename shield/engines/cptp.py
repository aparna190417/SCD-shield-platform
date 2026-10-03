from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CPTPStatus(StrEnum):
    """CPTP safety state."""

    SAFE = "safe"
    WARNING = "warning"
    CRITICAL = "critical"


class CPTPInput(BaseModel):
    """Validated telemetry input for the CPTP safety engine."""

    model_config = ConfigDict(extra="forbid")

    temperature_c: float = Field(ge=0.0, le=200.0)
    temperature_limit_c: float = Field(gt=0.0, le=200.0)

    power_w: float = Field(ge=0.0)
    power_limit_w: float = Field(gt=0.0)

    temperature_warning_percent: int = Field(
        default=80,
        ge=0,
        le=100,
    )
    power_warning_percent: int = Field(
        default=80,
        ge=0,
        le=100,
    )

    @model_validator(mode="after")
    def validate_limits(self) -> "CPTPInput":
        """Validate relationships between telemetry and configured limits."""

        if self.temperature_limit_c > 200:
            raise ValueError(
                "temperature_limit_c must not exceed the model limit of 200 C."
            )

        if self.temperature_c > self.temperature_limit_c:
            raise ValueError(
                "temperature_c cannot exceed temperature_limit_c."
            )

        if self.power_w > self.power_limit_w:
            raise ValueError("power_w cannot exceed power_limit_w.")

        return self


class CPTPResult(BaseModel):
    """Validated CPTP evaluation result."""

    model_config = ConfigDict(extra="forbid")

    status: CPTPStatus

    temperature_c: float
    temperature_limit_c: float

    power_w: float
    power_limit_w: float

    temperature_percent: int
    power_percent: int

    temperature_headroom_c: float
    power_headroom_w: float

    reason: str = Field(min_length=1)
    controls: list[str] = Field(default_factory=list)


class CPTPEngine:
    """Deterministic Compute Protection and Thermal Policy engine."""

    def evaluate(self, data: CPTPInput) -> CPTPResult:
        """Evaluate telemetry against warning and hard safety limits."""

        temperature_percent = int(
            data.temperature_c / data.temperature_limit_c * 100
        )
        power_percent = int(
            data.power_w / data.power_limit_w * 100
        )

        temperature_headroom = (
            data.temperature_limit_c - data.temperature_c
        )
        power_headroom = data.power_limit_w - data.power_w

        temperature_critical = (
            data.temperature_c >= data.temperature_limit_c
        )
        power_critical = data.power_w >= data.power_limit_w

        temperature_warning = (
            temperature_percent >= data.temperature_warning_percent
        )
        power_warning = power_percent >= data.power_warning_percent

        controls: list[str] = []

        if temperature_critical:
            controls.append("thermal_protection")
        elif temperature_warning:
            controls.append("thermal_mitigation")

        if power_critical:
            controls.append("power_protection")
        elif power_warning:
            controls.append("power_mitigation")

        if temperature_critical or power_critical:
            status = CPTPStatus.CRITICAL

            if temperature_critical and power_critical:
                reason = (
                    "Thermal and power hard safety limits have been reached."
                )
            elif temperature_critical:
                reason = "Thermal hard safety limit has been reached."
            else:
                reason = "Power hard safety limit has been reached."

        elif temperature_warning or power_warning:
            status = CPTPStatus.WARNING

            if temperature_warning and power_warning:
                reason = (
                    "Thermal and power warning thresholds have been reached."
                )
            elif temperature_warning:
                reason = "Thermal warning threshold has been reached."
            else:
                reason = "Power warning threshold has been reached."

        else:
            status = CPTPStatus.SAFE
            reason = "Thermal and power levels are within safe operating limits."

        return CPTPResult(
            status=status,
            temperature_c=data.temperature_c,
            temperature_limit_c=data.temperature_limit_c,
            power_w=data.power_w,
            power_limit_w=data.power_limit_w,
            temperature_percent=temperature_percent,
            power_percent=power_percent,
            temperature_headroom_c=temperature_headroom,
            power_headroom_w=power_headroom,
            reason=reason,
            controls=controls,
        )