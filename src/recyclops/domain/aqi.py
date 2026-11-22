"""India's National Air Quality Index (NAQI, CPCB method) from PM2.5 and PM10 concentrations.

The official index needs 24-hour averages and at least three pollutants, one of them PM. This app uses
the two PM pollutants only, so its figure is labelled "AQI (NAQI method, PM-based)".

CPCB publishes the breakpoints as integer ranges with gaps (PM2.5: 0-30, 31-60, ...), so a reading such
as 30.5 would fall in no range, and the top range is open-ended. The continuous form used here joins the
ranges at their shared edges and closes the top one, as common NAQI calculators do; at whole-number
readings inside a range it gives the same result as the published table.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from recyclops.domain.rounding import round_half_up


class Pollutant(StrEnum):
    PM25 = "pm25"
    PM10 = "pm10"


class Band(StrEnum):
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    MODERATE = "moderate"
    POOR = "poor"
    VERY_POOR = "very_poor"
    SEVERE = "severe"


MAX_AQI = 500
# Index value at each breakpoint, shared by both pollutants.
_INDEX_POINTS = (0, 50, 100, 200, 300, 400, MAX_AQI)
# Concentration (µg/m³, 24-hour average) at each breakpoint.
BREAKPOINTS: Mapping[Pollutant, tuple[float, ...]] = {
    Pollutant.PM25: (0, 30, 60, 90, 120, 250, 380),
    Pollutant.PM10: (0, 50, 100, 250, 350, 430, 510),
}
# Highest index in each band, in order.
_BAND_TOPS = (
    (50, Band.GOOD), (100, Band.SATISFACTORY), (200, Band.MODERATE),
    (300, Band.POOR), (400, Band.VERY_POOR), (MAX_AQI, Band.SEVERE),
)
# CPCB counts a 24-hour average as valid only with at least 16 hourly values.
MIN_HOURS_FOR_24H = 16


def sub_index(pollutant: Pollutant, concentration: float) -> int:
    """The pollutant's index, by linear interpolation between the two breakpoints around it."""
    if concentration < 0:
        raise ValueError("A concentration can't be negative.")
    points = BREAKPOINTS[pollutant]
    if concentration >= points[-1]:
        return MAX_AQI
    upper = next(i for i, point in enumerate(points) if concentration <= point and i > 0)
    c_lo, c_hi = points[upper - 1], points[upper]
    i_lo, i_hi = _INDEX_POINTS[upper - 1], _INDEX_POINTS[upper]
    return round_half_up(i_lo + (concentration - c_lo) * (i_hi - i_lo) / (c_hi - c_lo))


def band_for(aqi: int) -> Band:
    """The CPCB category of an index value (0-50 Good ... 401-500 Severe)."""
    if not 0 <= aqi <= MAX_AQI:
        raise ValueError(f"An AQI is between 0 and {MAX_AQI}.")
    return next(band for top, band in _BAND_TOPS if aqi <= top)


@dataclass(frozen=True)
class Aqi:
    value: int
    band: Band
    prominent: Pollutant  # the pollutant whose sub-index sets the AQI
    sub_indices: Mapping[Pollutant, int]


def aqi_from(concentrations: Mapping[Pollutant, float]) -> Aqi:
    """The AQI is the highest sub-index. On a tie, PM2.5 is named as prominent (it's listed first)."""
    if not concentrations:
        raise ValueError("At least one pollutant is needed.")
    subs = {pollutant: sub_index(pollutant, value) for pollutant, value in concentrations.items()}
    prominent = max((p for p in Pollutant if p in subs), key=lambda p: subs[p])
    return Aqi(value=subs[prominent], band=band_for(subs[prominent]), prominent=prominent, sub_indices=subs)


@dataclass(frozen=True)
class Average:
    value: float
    hours: int  # how many hourly values it's based on


def average_24h(hourly_values: Iterable[float | None]) -> Average | None:
    """Mean of one 24-hour window's hourly values, or None when fewer than 16 are usable.

    Missing hours (None) and negative readings (a known sensor artefact) don't count.
    """
    usable = [value for value in hourly_values if value is not None and value >= 0]
    if len(usable) > 24:
        raise ValueError("A 24-hour window has at most 24 hourly values.")
    if len(usable) < MIN_HOURS_FOR_24H:
        return None
    return Average(value=sum(usable) / len(usable), hours=len(usable))
