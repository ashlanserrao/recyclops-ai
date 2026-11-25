"""The live air provider: measured readings from OpenAQ and the modelled forecast from Open-Meteo, cached.

Per ~1 km square, a reading is reused for 15 minutes and a forecast for an hour, so repeat visits don't
repeat calls. The last good reading and forecast are kept as well. When OpenAQ is down, the plan uses the last
reading, marked stale with its original time. When Open-Meteo is down, the last forecast is used. With
nothing to fall back on there is no plan (503), never one built from made-up numbers.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from recyclops.core.cache import TTLCache
from recyclops.data.models import AirSnapshot, DataStatus, LiveDataUnavailableError, StationReading
from recyclops.data.open_meteo import SOURCE as FORECAST_SOURCE
from recyclops.data.open_meteo import OpenMeteo
from recyclops.data.openaq import OpenAQ
from recyclops.domain.forecast import Forecast, bias_factor

logger = logging.getLogger(__name__)

READING_TTL = 15 * 60
FORECAST_TTL = 60 * 60
# A reading older than this says too little about now to plan on, even marked stale.
LAST_READING_TTL = 6 * 60 * 60
LAST_FORECAST_TTL = 48 * 60 * 60  # the forecast covers two days
# What a source that is down or replying oddly raises (pydantic's ValidationError is a ValueError).
SOURCE_ERRORS = (httpx.HTTPError, ValueError)


@dataclass(frozen=True)
class _Lookup:
    reading: StationReading | None  # None: no station nearby is reporting (a real answer, so it's cached too)


def _now() -> datetime:
    return datetime.now(UTC)


class LiveAirProvider:
    def __init__(self, openaq: OpenAQ, open_meteo: OpenMeteo, now: Callable[[], datetime] = _now) -> None:
        self.openaq = openaq
        self.open_meteo = open_meteo
        self.now = now

        def cache[T](ttl: float) -> TTLCache[T]:
            return TTLCache(max_entries=512, ttl_seconds=ttl, clock=lambda: self.now().timestamp())

        self._readings: TTLCache[_Lookup] = cache(READING_TTL)
        self._last_readings: TTLCache[StationReading] = cache(LAST_READING_TTL)
        self._forecasts: TTLCache[dict[datetime, float]] = cache(FORECAST_TTL)
        self._last_forecasts: TTLCache[dict[datetime, float]] = cache(LAST_FORECAST_TTL)

    async def snapshot(self, lat: float, lon: float) -> AirSnapshot:
        key = f"{lat:.2f},{lon:.2f}"
        (status, reading), modelled = await asyncio.gather(self._measured(key, lat, lon),
                                                           self._modelled(key, lat, lon))
        forecast = Forecast.corrected(modelled, _bias(reading, modelled))
        return AirSnapshot(status=status, reading=reading, forecast=forecast, forecast_source=FORECAST_SOURCE)

    async def _measured(self, key: str, lat: float, lon: float) -> tuple[DataStatus, StationReading | None]:
        if (cached := self._readings.get(key)) is None:
            try:
                cached = _Lookup(await self.openaq.nearest_reading(lat, lon, self.now()))
            except SOURCE_ERRORS as exc:
                logger.warning("OpenAQ unavailable (%s), using the last good reading if any", _why(exc))
                last = self._last_readings.get(key)
                return (DataStatus.STALE, last) if last else (DataStatus.UNAVAILABLE, None)
            self._readings.set(key, cached)
            if cached.reading:
                self._last_readings.set(key, cached.reading)
        return (DataStatus.LIVE, cached.reading) if cached.reading else (DataStatus.UNAVAILABLE, None)

    async def _modelled(self, key: str, lat: float, lon: float) -> dict[datetime, float]:
        if (cached := self._forecasts.get(key)) is not None:
            return cached
        try:
            modelled = await self.open_meteo.modelled_pm25(lat, lon)
        except SOURCE_ERRORS as exc:
            logger.warning("Open-Meteo unavailable (%s), using the last forecast if any", _why(exc))
            if (last := self._last_forecasts.get(key)) is None:
                raise LiveDataUnavailableError from exc
            return last
        self._forecasts.set(key, modelled)
        self._last_forecasts.set(key, modelled)
        return modelled


def _bias(reading: StationReading | None, modelled: dict[datetime, float]) -> float | None:
    """measured ÷ modelled PM2.5 for the reading's hour, or None when either is missing (the raw model is used)."""
    if reading is None or reading.pm25_latest is None:
        return None
    hour_start = reading.measured_at - timedelta(hours=1)  # measured_at is the end of the hour
    if (model := modelled.get(hour_start)) is None:
        return None
    return bias_factor(reading.pm25_latest, model)


def _why(exc: Exception) -> str:
    """A short reason for the log: the status code or error type, never a URL or header."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    return type(exc).__name__
