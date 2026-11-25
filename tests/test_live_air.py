"""The live provider against faked OpenAQ and Open-Meteo replies, shaped like the real ones (spec V3-V6, E1-E3)."""

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
import respx

from recyclops.core.config import IST
from recyclops.data.live import LiveAirProvider
from recyclops.data.models import AirSnapshot, DataStatus, LiveDataUnavailableError
from recyclops.data.open_meteo import URL as OPEN_METEO_URL
from recyclops.data.open_meteo import OpenMeteo
from recyclops.data.openaq import BASE_URL, OpenAQ
from recyclops.domain.aqi import Average

HOUR = timedelta(hours=1)
NOW = datetime(2026, 11, 25, 4, 40, tzinfo=UTC)   # 10:10 IST
LAST_HOUR_END = datetime(2026, 11, 25, 3, 30, tzinfo=UTC)  # CPCB's latest hour: 08:00-09:00 IST
DELHI = (28.6139, 77.2090)


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def location(id_: int, name: str, km: float, last: datetime = LAST_HOUR_END, *, mobile: bool = False,
             sensors: tuple[tuple[str, int], ...] = (("pm25", 11), ("pm10", 12), ("no2", 13))) -> dict[str, Any]:
    return {"id": id_, "name": name, "distance": km * 1000, "isMobile": mobile, "provider": {"name": "CPCB"},
            "datetimeLast": {"utc": iso(last)},
            "sensors": [{"id": sid, "parameter": {"name": p, "units": "µg/m³"}} for p, sid in sensors]}


def hours(values: list[float | None], last_end: datetime = LAST_HOUR_END) -> dict[str, Any]:
    """Hourly results, oldest first, the last one ending at `last_end`."""
    ends = [last_end - HOUR * (len(values) - 1 - i) for i in range(len(values))]
    return {"results": [{"value": v, "period": {"label": "1hour", "datetimeFrom": {"utc": iso(end - HOUR)},
                                                 "datetimeTo": {"utc": iso(end)}}}
                        for v, end in zip(values, ends, strict=True)]}


def forecast(pm25_at_8am: float = 95.0) -> dict[str, Any]:
    """48 hours from 25 Nov 00:00 IST; 100 µg/m³ everywhere but 08:00, the hour the station last measured."""
    times = [(datetime(2026, 11, 25, tzinfo=IST) + HOUR * i).strftime("%Y-%m-%dT%H:%M") for i in range(48)]
    return {"hourly": {"time": times, "pm2_5": [pm25_at_8am if t.endswith("25T08:00") else 100.0 for t in times]}}


def snap(provider: LiveAirProvider, at: tuple[float, float] = DELHI) -> AirSnapshot:
    return asyncio.run(provider.snapshot(*at))


class Clock:
    def __init__(self) -> None:
        self.now = NOW

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def provider(clock: Clock) -> LiveAirProvider:
    client = httpx.AsyncClient()
    return LiveAirProvider(OpenAQ(client, "test-key"), OpenMeteo(client), now=clock)


@pytest.fixture
def api() -> Iterator[respx.MockRouter]:
    """Delhi: a dead station nearest, a mobile one next, then two reporting stations (the far one listed first)."""
    with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{BASE_URL}/v3/locations", name="locations").respond(json={"results": [
            location(2, "Far, Delhi - DPCC", 9.0, sensors=(("pm25", 21), ("pm10", 22))),
            location(3, "Closed in 2018, Delhi - CPCB", 0.5, last=datetime(2018, 2, 21, tzinfo=UTC)),
            location(4, "Sensor van", 1.0, mobile=True),
            location(1, "ITO, Delhi - CPCB", 2.34),
        ]})
        mock.get(f"{BASE_URL}/v3/sensors/11/hours", name="pm25").respond(json=hours([190.0] * 24))
        mock.get(f"{BASE_URL}/v3/sensors/12/hours", name="pm10").respond(json=hours([320.0] * 24))
        mock.get(OPEN_METEO_URL, name="forecast").respond(json=forecast())
        yield mock


def test_nearest_reporting_station_gives_the_aqi_and_corrects_the_forecast(
        provider: LiveAirProvider, api: respx.MockRouter) -> None:
    snapshot = snap(provider)
    reading = snapshot.reading
    assert snapshot.status is DataStatus.LIVE and reading is not None
    assert (reading.station.name, reading.station.distance_km) == ("ITO, Delhi - CPCB", 2.34)
    assert reading.measured_at == datetime(2026, 11, 25, 9, tzinfo=IST)
    assert reading.pm25_24h == Average(190.0, 24)
    assert reading.aqi and (reading.aqi.value, reading.aqi.band) == (354, "very_poor")  # G1's AQI
    assert reading.source == "OpenAQ (data: CPCB)"
    # Measured 190 against modelled 95 at 08:00: the whole day is scaled by 2.
    assert snapshot.forecast.bias == 2.0
    assert snapshot.forecast.hourly[datetime(2026, 11, 25, 13, tzinfo=IST)] == 200.0
    # The key travels in its header, and the search covers 25 km around the point.
    request = api["locations"].calls.last.request
    assert request.headers["X-API-Key"] == "test-key"
    assert (request.url.params["coordinates"], request.url.params["radius"]) == ("28.6139,77.209", "25000")


def test_repeat_visits_use_the_cache(provider: LiveAirProvider, api: respx.MockRouter, clock: Clock) -> None:
    snap(provider)
    clock.now += timedelta(minutes=10)
    snap(provider)
    assert [api[name].call_count for name in ("locations", "pm25", "pm10", "forecast")] == [1, 1, 1, 1]
    clock.now += timedelta(minutes=10)  # past the reading's 15 minutes, within the forecast's hour
    snap(provider)
    assert [api[name].call_count for name in ("locations", "forecast")] == [2, 1]


def test_source_down_uses_the_last_reading_marked_stale(
        provider: LiveAirProvider, api: respx.MockRouter, clock: Clock) -> None:
    snap(provider)
    clock.now += timedelta(minutes=20)
    api["locations"].respond(503)
    snapshot = snap(provider)
    assert snapshot.status is DataStatus.STALE
    assert snapshot.reading and snapshot.reading.measured_at == datetime(2026, 11, 25, 9, tzinfo=IST)


def test_source_down_with_nothing_kept_shows_no_aqi(provider: LiveAirProvider, api: respx.MockRouter) -> None:
    api["locations"].mock(side_effect=httpx.ConnectTimeout("slow"))
    snapshot = snap(provider)
    assert (snapshot.status, snapshot.reading, snapshot.forecast.bias) == (DataStatus.UNAVAILABLE, None, None)


def test_no_station_reporting_nearby_shows_no_aqi(provider: LiveAirProvider, api: respx.MockRouter) -> None:
    api["locations"].respond(json={"results": [location(3, "Closed", 0.5, last=datetime(2018, 2, 21, tzinfo=UTC))]})
    snapshot = snap(provider)
    assert (snapshot.status, snapshot.reading) == (DataStatus.UNAVAILABLE, None)
    assert snapshot.forecast.bias is None and snapshot.forecast.hourly  # forecast-only, uncorrected
    assert api["pm25"].call_count == 0


def test_a_station_whose_pm_stopped_is_skipped_for_the_next(
        provider: LiveAirProvider, api: respx.MockRouter) -> None:
    api["pm25"].respond(json=hours([190.0] * 24, last_end=LAST_HOUR_END - timedelta(hours=5)))
    api["pm10"].respond(json=hours([320.0] * 24, last_end=LAST_HOUR_END - timedelta(hours=5)))
    api.get(f"{BASE_URL}/v3/sensors/21/hours").respond(json=hours([100.0] * 24))
    api.get(f"{BASE_URL}/v3/sensors/22/hours").respond(json=hours([150.0] * 24))
    snapshot = snap(provider)
    assert snapshot.reading and snapshot.reading.station.name == "Far, Delhi - DPCC"


def test_too_few_hours_give_no_24h_average(provider: LiveAirProvider, api: respx.MockRouter) -> None:
    api["pm25"].respond(json=hours([None] * 9 + [190.0] * 15))  # 15 usable hours: below CPCB's 16
    snapshot = snap(provider)
    reading = snapshot.reading
    assert reading and reading.pm25_24h is None and reading.pm25_latest == 190.0
    assert reading.aqi and reading.aqi.prominent == "pm10"  # the AQI rests on PM10 alone


def test_forecast_down_uses_the_last_one_then_gives_up(
        provider: LiveAirProvider, api: respx.MockRouter, clock: Clock) -> None:
    snap(provider)
    clock.now += timedelta(hours=2)
    api["forecast"].respond(500)
    assert (snap(provider)).forecast.hourly  # the kept forecast
    with pytest.raises(LiveDataUnavailableError):
        snap(provider, (19.07, 72.88))  # nothing kept for Mumbai


def test_an_unexpected_reply_counts_as_down(provider: LiveAirProvider, api: respx.MockRouter) -> None:
    api["locations"].respond(json={"unexpected": True})
    assert (snap(provider)).status is DataStatus.UNAVAILABLE
