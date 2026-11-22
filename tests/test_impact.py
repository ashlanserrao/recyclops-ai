"""Impact numbers (spec V8, V9) and indoor actions, against the cited factors."""

from datetime import time

import pytest

from recyclops.domain.factors import inhalation_rate
from recyclops.domain.forecast import at, day_windows
from recyclops.domain.home import HomeAction, home_actions
from recyclops.domain.household import Commute, CommuteMode, CookingFuel, Home, Intensity
from recyclops.domain.impact import (
    Alternative,
    indoor_exposure_cut_pct,
    purifier_cadr_needed,
    transport_swaps,
)
from tests.golden import DAY, G1_FORECAST, G1_HOUSEHOLD, G1_PARENT, G3_STUDENT, forecast


def test_g1_parent_car_swaps_best_first() -> None:
    assert G1_PARENT.commute is not None
    swaps = transport_swaps(G1_PARENT.commute, city_has_metro=True)
    # 150 km a week at 0.140 kg/km by car vs 0.00795 metro, 0.015161 bus, 0.140/3 carpool.
    assert [(s.alternative, s.co2_kg_saved_per_week, s.vehicle_km_off_road_per_week) for s in swaps] == [
        (Alternative.METRO, 19.8, 150.0), (Alternative.BUS, 18.7, 150.0), (Alternative.CARPOOL, 14.0, 100.0)]


def test_g3_bus_rider_gains_a_little_from_metro() -> None:
    assert G3_STUDENT.commute is not None
    swaps = transport_swaps(G3_STUDENT.commute, city_has_metro=True)
    assert [(s.alternative, s.co2_kg_saved_per_week, s.vehicle_km_off_road_per_week) for s in swaps] == [
        (Alternative.METRO, 0.7, 0.0)]  # 100 km × (0.015161 − 0.00795); the bus runs anyway


def test_no_metro_offered_where_there_is_none() -> None:
    commute = Commute(mode=CommuteMode.TWO_WHEELER, one_way_km=8, days_per_week=6, departs=time(9))
    assert [s.alternative for s in transport_swaps(commute, city_has_metro=False)] == [Alternative.BUS]


def test_low_emission_commutes_get_no_swap() -> None:
    commute = Commute(mode=CommuteMode.METRO, one_way_km=12, days_per_week=5, departs=time(9))
    assert transport_swaps(commute, city_has_metro=True) == []


@pytest.mark.parametrize(("age", "intensity", "purifier", "cut"), [
    (8, Intensity.MODERATE, False, 50),   # calmer breathing only: 1 - 0.011/0.022
    (30, Intensity.MODERATE, True, 76),   # 1 - 0.51 × 0.012/0.026
    (68, Intensity.LIGHT, False, 0),      # same effort, same air: staying in alone doesn't help
    (68, Intensity.LIGHT, True, 49),      # the purifier's share
])
def test_indoor_exposure_cut(age: int, intensity: Intensity, purifier: bool, cut: int) -> None:
    assert indoor_exposure_cut_pct(age, intensity, purifier) == cut


@pytest.mark.parametrize(("age", "rate"), [(1, 0.021), (8, 0.022), (65, 0.026), (90, 0.025)])
def test_inhalation_rate_age_bands(age: int, rate: float) -> None:
    assert inhalation_rate(age, Intensity.MODERATE) == rate


def test_purifier_size_for_room() -> None:
    assert purifier_cadr_needed(15) == 225  # 15 m² × 3 m × 5 air changes an hour


def test_g1_home_actions() -> None:
    windows = day_windows(G1_FORECAST, DAY)
    assert windows is not None
    advice = home_actions(G1_HOUSEHOLD.home, windows)
    assert [a.action for a in advice] == [
        HomeAction.KEEP_WINDOWS_SHUT, HomeAction.AIR_OUT_IN_BEST_WINDOW, HomeAction.CLOSE_ROAD_SIDE,
        HomeAction.CONSIDER_PURIFIER, HomeAction.USE_KITCHEN_EXHAUST, HomeAction.WET_MOP,
        HomeAction.NO_INCENSE_OR_COILS]
    assert (advice[0].at, advice[1].at, advice[3].indoor_pm_cut_pct) == (
        at(DAY, time(20)), at(DAY, time(13)), 49)


def test_clean_day_needs_only_airing_out() -> None:
    windows = day_windows(forecast(40), DAY)
    assert windows is not None
    home = Home(has_purifier=True, purifier_room_m2=15, cooking_fuel=CookingFuel.LPG, faces_main_road=True)
    assert [a.action for a in home_actions(home, windows)] == [HomeAction.AIR_OUT_IN_BEST_WINDOW]


def test_purifier_owner_gets_sizing_and_biomass_switch() -> None:
    windows = day_windows(G1_FORECAST, DAY)
    assert windows is not None
    home = Home(has_purifier=True, purifier_room_m2=15, cooking_fuel=CookingFuel.BIOMASS, faces_main_road=False)
    run, switch = (next(a for a in home_actions(home, windows) if a.action is action)
                   for action in (HomeAction.RUN_PURIFIER, HomeAction.SWITCH_FROM_BIOMASS))
    assert (run.indoor_pm_cut_pct, run.purifier_cadr_m3h, switch.action) == (
        49, 225, HomeAction.SWITCH_FROM_BIOMASS)
