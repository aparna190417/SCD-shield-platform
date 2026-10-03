import pytest
from pydantic import ValidationError

from shield.engines.cptp import (
    CPTPEngine,
    CPTPInput,
    CPTPStatus,
)


@pytest.fixture
def engine() -> CPTPEngine:
    return CPTPEngine()


def make_input(**overrides: int) -> CPTPInput:
    values = {
        "temperature_c": 60,
        "temperature_limit_c": 90,
        "power_w": 300,
        "power_limit_w": 500,
    }
    values.update(overrides)
    return CPTPInput(**values)


class TestCPTPEngine:
    def test_safe_when_telemetry_is_below_warning_threshold(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            make_input(
                temperature_c=60,
                power_w=300,
            )
        )

        assert result.status == CPTPStatus.SAFE
        assert result.temperature_percent == 66
        assert result.power_percent == 60
        assert result.controls == []

    def test_warning_when_temperature_reaches_warning_threshold(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            make_input(
                temperature_c=72,
                power_w=300,
            )
        )

        assert result.status == CPTPStatus.WARNING
        assert result.temperature_percent == 80
        assert result.power_percent == 60
        assert result.controls == ["thermal_mitigation"]

    def test_warning_when_power_reaches_warning_threshold(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            make_input(
                temperature_c=60,
                power_w=400,
            )
        )

        assert result.status == CPTPStatus.WARNING
        assert result.temperature_percent == 66
        assert result.power_percent == 80
        assert result.controls == ["power_mitigation"]

    def test_warning_when_temperature_and_power_reach_threshold(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            make_input(
                temperature_c=72,
                power_w=400,
            )
        )

        assert result.status == CPTPStatus.WARNING
        assert result.controls == [
            "thermal_mitigation",
            "power_mitigation",
        ]

    def test_critical_when_temperature_reaches_hard_limit(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            make_input(
                temperature_c=90,
                power_w=300,
            )
        )

        assert result.status == CPTPStatus.CRITICAL
        assert result.temperature_percent == 100
        assert result.temperature_headroom_c == 0
        assert result.controls == ["thermal_protection"]

    def test_critical_when_power_reaches_hard_limit(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            make_input(
                temperature_c=60,
                power_w=500,
            )
        )

        assert result.status == CPTPStatus.CRITICAL
        assert result.power_percent == 100
        assert result.power_headroom_w == 0
        assert result.controls == ["power_protection"]

    def test_critical_when_both_hard_limits_are_reached(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            make_input(
                temperature_c=90,
                power_w=500,
            )
        )

        assert result.status == CPTPStatus.CRITICAL
        assert result.controls == [
            "thermal_protection",
            "power_protection",
        ]

    def test_headroom_is_calculated_correctly(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            make_input(
                temperature_c=70,
                power_w=350,
            )
        )

        assert result.temperature_headroom_c == 20
        assert result.power_headroom_w == 150

    def test_percentage_uses_integer_arithmetic(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            make_input(
                temperature_c=61,
                power_w=333,
            )
        )

        assert result.temperature_percent == 67
        assert result.power_percent == 66

    def test_custom_warning_thresholds_are_respected(
        self,
        engine: CPTPEngine,
    ) -> None:
        result = engine.evaluate(
            CPTPInput(
                temperature_c=70,
                temperature_limit_c=100,
                power_w=300,
                power_limit_w=500,
                temperature_warning_percent=70,
                power_warning_percent=90,
            )
        )

        assert result.status == CPTPStatus.WARNING
        assert result.controls == ["thermal_mitigation"]

    def test_invalid_negative_temperature_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_input(temperature_c=-1)

    def test_invalid_power_limit_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_input(power_limit_w=0)

    def test_temperature_above_model_limit_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_input(temperature_c=201)

    def test_warning_threshold_above_100_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CPTPInput(
                temperature_c=60,
                temperature_limit_c=90,
                power_w=300,
                power_limit_w=500,
                temperature_warning_percent=101,
            )

    def test_result_is_serializable(self, engine: CPTPEngine) -> None:
        result = engine.evaluate(make_input())

        payload = result.model_dump()

        assert payload["status"] == CPTPStatus.SAFE
        assert payload["temperature_c"] == 60
        assert payload["power_w"] == 300