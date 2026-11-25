"""OpenAQ v3: the nearest monitoring station that is still reporting, and its last 24 hours of PM.

A lookup makes up to three calls: the stations within 25 km, then the PM2.5 and PM10 hourly values side by
side. Many listed stations stopped reporting years ago, so a station counts only if it reported within the
last 3 hours. The API doesn't sort by distance, so every station in range is fetched and sorted here.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
from pydantic import BaseModel, Field

from recyclops.core.config import IST
from recyclops.data.models import Station, StationReading
from recyclops.domain.aqi import Average, average_24h

BASE_URL = "https://api.openaq.org"
RADIUS_M = 25_000          # the API's maximum, and the spec's "nearby"
MAX_AGE = timedelta(hours=3)
STATIONS_TRIED = 2         # if the nearest has no recent PM values, one more before giving up
PAGE_LIMIT = 1000          # a big city has more than 100 locations in range
DAY = timedelta(hours=24)
PM = ("pm25", "pm10")


# The parts of OpenAQ's responses the app reads; anything else in them is ignored.
class _Time(BaseModel):
    utc: datetime


class _Named(BaseModel):
    name: str


class _Sensor(BaseModel):
    id: int
    parameter: _Named


class _Location(BaseModel):
    id: int
    name: str
    distance: float | None = None  # metres from the query point
    is_mobile: bool = Field(False, alias="isMobile")
    provider: _Named | None = None
    datetime_last: _Time | None = Field(None, alias="datetimeLast")
    sensors: list[_Sensor] = []


class _Locations(BaseModel):
    results: list[_Location]


class _Period(BaseModel):
    datetime_to: _Time = Field(alias="datetimeTo")


class _Hour(BaseModel):
    value: float | None
    period: _Period


class _Hours(BaseModel):
    results: list[_Hour]


@dataclass(frozen=True)
class _Value:
    end: datetime  # end of the hour it averages (UTC)
    value: float


class OpenAQ:
    def __init__(self, client: httpx.AsyncClient, api_key: str, timeout: float = 8.0) -> None:
        self.client = client
        self._headers = {"X-API-Key": api_key}
        self.timeout = timeout

    async def nearest_reading(self, lat: float, lon: float, now: datetime) -> StationReading | None:
        """The nearest reporting station's reading, or None when no station within 25 km is reporting.

        Raises httpx.HTTPError or ValueError (an unexpected reply) when the source can't be read.
        """
        found = await self._get(_Locations, "/v3/locations", coordinates=f"{lat},{lon}", radius=RADIUS_M,
                                limit=PAGE_LIMIT)
        for location in _reporting(found.results, now)[:STATIONS_TRIED]:
            if reading := await self._reading(location, now):
                return reading
        return None

    async def _reading(self, location: _Location, now: datetime) -> StationReading | None:
        sensors = {s.parameter.name: s.id for s in location.sensors if s.parameter.name in PM}
        series = dict(zip(sensors, await asyncio.gather(*(self._hours(id_, now) for id_ in sensors.values())),
                          strict=True))
        # The reading's time is its latest PM2.5 hour (PM10's when there's no PM2.5): the hour the
        # forecast is corrected against.
        latest = next((s[-1] for name in PM if (s := series.get(name))), None)
        if latest is None or now - latest.end > MAX_AGE:
            return None
        pm25 = series.get("pm25", [])
        provider = location.provider.name if location.provider else ""
        return StationReading(
            station=Station(id=str(location.id), name=location.name, distance_km=(location.distance or 0) / 1000),
            measured_at=latest.end.astimezone(IST),
            pm25_24h=_average(pm25, latest.end),
            pm10_24h=_average(series.get("pm10", []), latest.end),
            pm25_latest=pm25[-1].value if pm25 and pm25[-1].end == latest.end else None,
            source=f"OpenAQ (data: {provider})" if provider and provider != "N/A" else "OpenAQ",
        )

    async def _hours(self, sensor_id: int, now: datetime) -> list[_Value]:
        """The sensor's hourly values from the last 25 hours, oldest first, without missing or negative ones."""
        hours = await self._get(_Hours, f"/v3/sensors/{sensor_id}/hours", limit=48,
                                datetime_from=(now - DAY - timedelta(hours=1)).isoformat(timespec="seconds"),
                                datetime_to=now.isoformat(timespec="seconds"))
        by_end = {h.period.datetime_to.utc: h.value for h in hours.results if h.value is not None and h.value >= 0}
        return [_Value(end, value) for end, value in sorted(by_end.items())]

    async def _get[M: BaseModel](self, model: type[M], path: str, **params: str | int) -> M:
        response = await self.client.get(BASE_URL + path, params=params, headers=self._headers, timeout=self.timeout)
        response.raise_for_status()
        return model.model_validate_json(response.content)


def _reporting(locations: list[_Location], now: datetime) -> list[_Location]:
    """Fixed stations in range with a PM sensor that reported within MAX_AGE, nearest first."""
    usable = [
        loc for loc in locations
        if not loc.is_mobile and loc.distance is not None and loc.distance <= RADIUS_M
        and loc.datetime_last and now - loc.datetime_last.utc <= MAX_AGE
        and any(s.parameter.name in PM for s in loc.sensors)
    ]
    return sorted(usable, key=lambda loc: loc.distance or 0)


def _average(values: list[_Value], until: datetime) -> Average | None:
    """The 24-hour average ending at `until` (None below CPCB's 16-hour minimum)."""
    return average_24h(v.value for v in values if until - DAY < v.end <= until)
