"""POST /api/plan end to end with a fake air provider (spec G1, V3, V13, E1)."""

from collections.abc import Iterator
from datetime import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from recyclops.api.dependencies import get_air_provider, today_in_india
from recyclops.api.main import app
from recyclops.data.models import AirSnapshot, DataStatus, Station, StationReading
from recyclops.domain.aqi import Average
from recyclops.domain.cities import nearest_city
from recyclops.domain.forecast import Forecast, at
from tests.frontend_fixtures import assert_matches_fixture
from tests.golden import DAY, G1_FORECAST, G1_HOUSEHOLD

DELHI = {"lat": 28.6139, "lon": 77.2090}
G1_READING = StationReading(
    station=Station(id="delhi-1", name="ITO, Delhi - CPCB", distance_km=2.34),
    measured_at=at(DAY, time(12)), pm25_24h=Average(190, 24), pm10_24h=Average(320, 24), pm25_latest=150,
    source="OpenAQ (data: CPCB)")


class FakeProvider:
    def __init__(self, snapshot: AirSnapshot) -> None:
        self.snapshot_value = snapshot
        self.calls: list[tuple[float, float]] = []

    async def snapshot(self, lat: float, lon: float) -> AirSnapshot:
        self.calls.append((lat, lon))
        return self.snapshot_value


def live(reading: StationReading | None = G1_READING, forecast: Forecast = G1_FORECAST,
         status: DataStatus = DataStatus.LIVE) -> AirSnapshot:
    return AirSnapshot(status=status, reading=reading, forecast=forecast, forecast_source="Open-Meteo (CAMS)")


@pytest.fixture
def plan_client(client: TestClient) -> Iterator[TestClient]:
    app.dependency_overrides[get_air_provider] = lambda: FakeProvider(live())
    app.dependency_overrides[today_in_india] = lambda: DAY
    yield client


def body(location: dict[str, float] = DELHI, **changes: Any) -> dict[str, Any]:
    return {"location": location, "household": G1_HOUSEHOLD.model_dump(mode="json"), **changes}


def test_g1_delhi_plan(plan_client: TestClient) -> None:
    response = plan_client.post("/api/plan", json=body())
    assert response.status_code == 200
    plan = response.json()
    assert (plan["city"], plan["day"]) == ("Delhi", "2026-11-25")
    assert plan["air"]["aqi"] == {"value": 354, "band": "very_poor", "prominent": "pm25",
                                  "method": "NAQI method, PM-based (24-hour averages of PM2.5 and PM10)"}
    assert plan["air"]["station"] == {"name": "ITO, Delhi - CPCB", "distance_km": 2.3}
    assert plan["windows"]["best"]["start"] == "2026-11-25T13:00:00+05:30"

    child, grandmother, parent = plan["members"]
    play = child["decisions"][0]
    assert (play["action"], play["new_start"], play["new_duration_min"], play["exposure_cut_pct"]) == (
        "move", "2026-11-25T13:00:00+05:30", 30, 77)
    walk = grandmother["decisions"][0]
    assert (walk["action"], walk["exposure_cut_pct"]) == ("indoor", 0)  # no purifier at home: honest zero
    assert [s["alternative"] for s in parent["commute"]["swaps"]] == ["metro", "bus", "carpool"]
    assert {a["action"] for a in plan["home"]} >= {"keep_windows_shut", "consider_purifier", "wet_mop"}
    assert plan["sources"]  # every number's source travels with it


def test_frontend_fixture_is_the_real_g1_plan(plan_client: TestClient) -> None:
    assert_matches_fixture("plan-delhi.json", plan_client.post("/api/plan", json=body()).json())


def test_no_station_nearby_shows_no_aqi(client: TestClient) -> None:
    app.dependency_overrides[get_air_provider] = lambda: FakeProvider(live(reading=None, status=DataStatus.UNAVAILABLE))
    app.dependency_overrides[today_in_india] = lambda: DAY
    air = client.post("/api/plan", json=body()).json()["air"]
    assert (air["status"], air["aqi"], air["station"], air["forecast_corrected"]) == (
        "unavailable", None, None, False)


def test_without_live_data_source_says_so(client: TestClient) -> None:
    response = client.post("/api/plan", json=body())  # the real provider isn't configured in tests
    assert response.status_code == 503
    assert response.json() == {"error": "Live air-quality data isn't available right now. Please try again later."}


def test_city_label_follows_location() -> None:
    mumbai, nagpur_outskirts, sea = nearest_city(19.07, 72.88), nearest_city(21.2, 79.1), nearest_city(15.0, 70.0)
    assert (mumbai and mumbai.name, nagpur_outskirts and nagpur_outskirts.name, sea) == ("Mumbai", "Nagpur", None)


@pytest.mark.parametrize("bad", [
    body(location={"lat": 51.5, "lon": -0.1}),                               # outside India
    body(extra="field"),                                                     # unknown field
    {**body(), "household": {**body()["household"],
                             "members": [body()["household"]["members"][0]] * 6}},  # too many members
    {**body(), "household": {**body()["household"], "members": [
        {**body()["household"]["members"][0], "name": "x" * 31}]}},          # name too long
])
def test_bad_requests_get_clean_422(plan_client: TestClient, bad: dict[str, Any]) -> None:
    response = plan_client.post("/api/plan", json=bad)
    assert response.status_code == 422
    assert response.json()["error"] == "Please check the highlighted fields."
    assert "x" * 31 not in response.text  # submitted values are never echoed


def test_field_errors_point_at_the_field_in_plain_words(plan_client: TestClient) -> None:
    late_walk = {"kind": "walk", "start": "23:30", "duration_min": 60, "intensity": "light"}
    member = {**body()["household"]["members"][0], "activities": [late_walk]}
    bad = {**body(), "household": {**body()["household"], "members": [member]}}
    fields = plan_client.post("/api/plan", json=bad).json()["fields"]
    assert fields == [{"field": "household.members.0.activities.0", "message": "An activity must end by midnight."}]


def test_cities_list_matches_the_planner(client: TestClient) -> None:
    response = client.get("/api/cities")
    cities = response.json()
    names = [city["name"] for city in cities]
    assert names == sorted(names) and len(names) == len(set(names))
    assert {"name": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639, "has_metro": True} in cities
    assert response.headers["cache-control"] == "public, max-age=86400"
