from hypothesis import given
from hypothesis import strategies as st

from shield.engines.cptp import (
    CPTPEngine,
    CPTPInput,
    CPTPStatus,
)


@st.composite
def safe_telemetry(draw: st.DrawFn) -> CPTPInput:
    temperature_limit = draw(
        st.integers(min_value=10, max_value=200)
    )
    power_limit = draw(
        st.integers(min_value=100, max_value=2000)
    )

    temperature = draw(
        st.integers(
            min_value=0,
            max_value=temperature_limit - 1,
        )
    )
    power = draw(
        st.integers(
            min_value=0,
            max_value=power_limit - 1,
        )
    )

    return CPTPInput(
        temperature_c=temperature,
        temperature_limit_c=temperature_limit,
        power_w=power,
        power_limit_w=power_limit,
    )


@given(safe_telemetry())
def test_safe_telemetry_never_returns_critical(
    telemetry: CPTPInput,
) -> None:
    result = CPTPEngine().evaluate(telemetry)

    assert result.status != CPTPStatus.CRITICAL


@given(
    st.integers(min_value=10, max_value=200),
    st.integers(min_value=100, max_value=2000),
)
def test_temperature_hard_limit_always_produces_critical(
    temperature_limit: int,
    power_limit: int,
) -> None:
    telemetry = CPTPInput(
        temperature_c=temperature_limit,
        temperature_limit_c=temperature_limit,
        power_w=0,
        power_limit_w=power_limit,
    )

    result = CPTPEngine().evaluate(telemetry)

    assert result.status == CPTPStatus.CRITICAL
    assert "Thermal" in result.reason


@given(
    st.integers(min_value=10, max_value=200),
    st.integers(min_value=100, max_value=2000),
)
def test_power_hard_limit_always_produces_critical(
    temperature_limit: int,
    power_limit: int,
) -> None:
    telemetry = CPTPInput(
        temperature_c=0,
        temperature_limit_c=temperature_limit,
        power_w=power_limit,
        power_limit_w=power_limit,
    )

    result = CPTPEngine().evaluate(telemetry)

    assert result.status == CPTPStatus.CRITICAL
    assert "Power" in result.reason


@given(
    st.integers(min_value=10, max_value=200),
    st.integers(min_value=100, max_value=2000),
)
def test_temperature_warning_threshold_produces_warning(
    temperature_limit: int,
    power_limit: int,
) -> None:
    temperature = (temperature_limit * 80 + 99) // 100

    if temperature >= temperature_limit:
        temperature = temperature_limit - 1

    telemetry = CPTPInput(
        temperature_c=temperature,
        temperature_limit_c=temperature_limit,
        power_w=0,
        power_limit_w=power_limit,
    )

    result = CPTPEngine().evaluate(telemetry)

    assert result.status == CPTPStatus.WARNING


@given(
    st.integers(min_value=10, max_value=200),
    st.integers(min_value=100, max_value=2000),
)
def test_power_warning_threshold_produces_warning(
    temperature_limit: int,
    power_limit: int,
) -> None:
    power = (power_limit * 80 + 99) // 100

    if power >= power_limit:
        power = power_limit - 1

    telemetry = CPTPInput(
        temperature_c=0,
        temperature_limit_c=temperature_limit,
        power_w=power,
        power_limit_w=power_limit,
    )

    result = CPTPEngine().evaluate(telemetry)

    assert result.status == CPTPStatus.WARNING


@given(
    st.integers(min_value=10, max_value=200),
    st.integers(min_value=100, max_value=2000),
)
def test_cptp_percentages_never_exceed_hundred(
    temperature_limit: int,
    power_limit: int,
) -> None:
    telemetry = CPTPInput(
        temperature_c=temperature_limit,
        temperature_limit_c=temperature_limit,
        power_w=power_limit,
        power_limit_w=power_limit,
    )

    result = CPTPEngine().evaluate(telemetry)

    assert 0 <= result.temperature_percent <= 100
    assert 0 <= result.power_percent <= 100


@given(
    st.integers(min_value=10, max_value=200),
    st.integers(min_value=100, max_value=2000),
)
def test_hard_limits_leave_zero_headroom(
    temperature_limit: int,
    power_limit: int,
) -> None:
    telemetry = CPTPInput(
        temperature_c=temperature_limit,
        temperature_limit_c=temperature_limit,
        power_w=power_limit,
        power_limit_w=power_limit,
    )

    result = CPTPEngine().evaluate(telemetry)

    assert result.temperature_headroom_c == 0
    assert result.power_headroom_w == 0