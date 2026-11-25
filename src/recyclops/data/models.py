"""What the data layer hands the rest of the app, whichever source the numbers came from."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from recyclops.domain.aqi import Aqi, Average, Pollutant, aqi_from
from recyclops.domain.forecast import Forecast


class DataStatus(StrEnum):
    LIVE = "live"                # a fresh reading from a station within range
    STALE = "stale"              # the source is down: the last good reading, with its original time
    UNAVAILABLE = "unavailable"  # no station within range, or nothing cached: no AQI is shown


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    distance_km: float


@dataclass(frozen=True)
class StationReading:
    station: Station
    measured_at: datetime        # time of the latest hourly value
    pm25_24h: Average | None     # None when fewer than 16 of the last 24 hours were reported
    pm10_24h: Average | None
    pm25_latest: float | None    # the latest hourly value, used to correct the forecast
    source: str                  # attribution shown next to the numbers

    @property
    def aqi(self) -> Aqi | None:
        averages = {Pollutant.PM25: self.pm25_24h, Pollutant.PM10: self.pm10_24h}
        concentrations = {p: a.value for p, a in averages.items() if a is not None}
        return aqi_from(concentrations) if concentrations else None


@dataclass(frozen=True)
class AirSnapshot:
    status: DataStatus
    reading: StationReading | None
    forecast: Forecast           # corrected against the reading when there is one
    forecast_source: str


class AirProvider(Protocol):
    async def snapshot(self, lat: float, lon: float) -> AirSnapshot: ...


class LiveDataUnavailableError(RuntimeError):
    """There's no forecast to plan from: the source is down and nothing is cached. Never filled with made-up data."""


class LiveDataNotConfiguredError(LiveDataUnavailableError):
    """No real data source is set up (no OpenAQ key)."""


class NotConfiguredProvider:
    async def snapshot(self, lat: float, lon: float) -> AirSnapshot:
        raise LiveDataNotConfiguredError
