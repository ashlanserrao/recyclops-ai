"""Forecast correction and time windows (spec V6)."""

from datetime import time

import pytest

from recyclops.domain.aqi import Band
from recyclops.domain.forecast import BIAS_MAX, BIAS_MIN, Forecast, at, bias_factor, day_windows, hourly_band
from tests.golden import DAY, G1_FORECAST, G2_FORECAST, G3_FORECAST, forecast


@pytest.mark.parametrize(("measured", "modelled", "factor"), [
    (200, 100, 2.0), (80, 10, BIAS_MAX), (20, 100, BIAS_MIN), (50, 0, BIAS_MAX), (0, 0, 1.0),
])
def test_bias_factor_is_clamped(measured: float, modelled: float, factor: float) -> None:
    assert bias_factor(measured, modelled) == factor


def test_correction_scales_every_hour() -> None:
    modelled = {at(DAY, time(9)): 50.0, at(DAY, time(10)): 40.0}
    corrected = Forecast.corrected(modelled, 2.0)
    assert corrected.hourly == {at(DAY, time(9)): 100.0, at(DAY, time(10)): 80.0}
    assert corrected.bias == 2.0
    assert Forecast.corrected(modelled, None).bias is None


def test_mean_over_covers_every_hour_touched() -> None:
    day = forecast(100, h17_17=200)
    assert day.mean_over(at(DAY, time(16, 30)), 60) == 150  # 16:30-17:30 touches hours 16 and 17
    assert day.mean_over(at(DAY, time(17)), 30) == 200


def test_mean_over_is_none_beyond_the_forecast() -> None:
    assert Forecast({at(DAY, time(9)): 50.0}).mean_over(at(DAY, time(9, 30)), 60) is None


@pytest.mark.parametrize(("day_forecast", "best", "worst"), [
    (G1_FORECAST, 13, 20), (G2_FORECAST, 10, 6), (G3_FORECAST, 12, 17),
])
def test_golden_windows(day_forecast: Forecast, best: int, worst: int) -> None:
    windows = day_windows(day_forecast, DAY)
    assert windows is not None
    assert (windows.best.start, windows.worst.start) == (at(DAY, time(best)), at(DAY, time(worst)))
    assert windows.best.end == at(DAY, time(best + 2))


def test_windows_tie_goes_to_the_earliest() -> None:
    windows = day_windows(forecast(80), DAY)
    assert windows is not None
    assert windows.best.start == windows.worst.start == at(DAY, time(6))


def test_no_windows_without_forecast() -> None:
    assert day_windows(Forecast({}), DAY) is None


def test_hourly_band_uses_pm25_breakpoints() -> None:
    assert [hourly_band(v) for v in (40, 70, 105, 230, 300)] == [
        Band.SATISFACTORY, Band.MODERATE, Band.POOR, Band.VERY_POOR, Band.SEVERE]
