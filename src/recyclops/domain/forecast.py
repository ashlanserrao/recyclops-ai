"""The hourly PM2.5 forecast: corrected against the live reading, banded, and searched for time windows.

The forecast is modelled (CAMS, ~45 km grid), not measured. Its level can be far off for Indian cities,
but the shape of the day (which hours are cleaner) is what the windows need. Scaling the whole day by
measured ÷ modelled at the current hour keeps that shape and anchors the level to the real reading.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from recyclops.core.config import IST
from recyclops.domain.aqi import Band, Pollutant, band_for, sub_index

# Limits on the correction, so one odd reading (a sensor spike, a bad model hour) can't distort the day.
BIAS_MIN, BIAS_MAX = 0.5, 3.0
WINDOW_HOURS = 2
FIRST_WINDOW_START = 6   # 06:00-08:00
LAST_WINDOW_START = 20   # 20:00-22:00
HOUR = timedelta(hours=1)


def bias_factor(measured_pm25: float, modelled_pm25: float) -> float:
    """measured ÷ modelled for the same hour, within [BIAS_MIN, BIAS_MAX]."""
    if modelled_pm25 <= 0:
        return BIAS_MAX if measured_pm25 > 0 else 1.0
    return min(max(measured_pm25 / modelled_pm25, BIAS_MIN), BIAS_MAX)


def hourly_band(pm25: float) -> Band:
    """The band an hourly value falls in, using the 24-hour breakpoints: an indication, not an official AQI."""
    return band_for(sub_index(Pollutant.PM25, pm25))


@dataclass(frozen=True)
class Forecast:
    """Hourly PM2.5 in µg/m³, keyed by the start of each hour (IST)."""
    hourly: Mapping[datetime, float]
    # The correction applied, or None when there was no live reading to correct against.
    bias: float | None = None

    @classmethod
    def corrected(cls, modelled: Mapping[datetime, float], factor: float | None) -> "Forecast":
        if factor is None:
            return cls(dict(modelled))
        return cls({hour: value * factor for hour, value in modelled.items()}, bias=factor)

    def mean_over(self, start: datetime, minutes: int) -> float | None:
        """Mean PM2.5 over the hours a slot touches, or None if the forecast doesn't cover them all."""
        hour = start.replace(minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=minutes)
        values = []
        while hour < end:
            if hour not in self.hourly:
                return None
            values.append(self.hourly[hour])
            hour += HOUR
        return sum(values) / len(values)


@dataclass(frozen=True)
class Window:
    start: datetime
    mean_pm25: float

    @property
    def end(self) -> datetime:
        return self.start + WINDOW_HOURS * HOUR

    @property
    def band(self) -> Band:
        return hourly_band(self.mean_pm25)


@dataclass(frozen=True)
class DayWindows:
    best: Window
    worst: Window


def at(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock, tzinfo=IST)


def day_windows(forecast: Forecast, day: date) -> DayWindows | None:
    """The cleanest and dirtiest 2-hour blocks between 06:00 and 22:00; on a tie, the earlier one.

    None when the forecast covers none of the day's blocks.
    """
    candidates = []
    for start_hour in range(FIRST_WINDOW_START, LAST_WINDOW_START + 1):
        start = at(day, time(start_hour))
        mean = forecast.mean_over(start, WINDOW_HOURS * 60)
        if mean is not None:
            candidates.append(Window(start, mean))
    if not candidates:
        return None
    # min/max return the first of equal values, and candidates run earliest first.
    return DayWindows(best=min(candidates, key=lambda w: w.mean_pm25),
                      worst=max(candidates, key=lambda w: w.mean_pm25))
