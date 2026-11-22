"""The size of a choice's effect, as numbers computed from the cited factors (factors.py).

Two kinds: what the household breathes in (exposure), and what it puts into the city's air (emissions).
"""

from dataclasses import dataclass
from enum import StrEnum

from recyclops.domain.factors import (
    CARPOOL_OCCUPANCY,
    CO2_PER_KM,
    INDOOR_TO_OUTDOOR,
    PURIFIER_AIR_CHANGES_PER_HOUR,
    PURIFIER_REDUCTION,
    ROOM_HEIGHT_M,
    inhalation_rate,
)
from recyclops.domain.household import Commute, CommuteMode, Intensity
from recyclops.domain.rounding import round_half_up

# Modes whose trips put a vehicle on the road for this traveller alone.
PRIVATE_VEHICLES = {CommuteMode.CAR, CommuteMode.TWO_WHEELER, CommuteMode.AUTO}
# Already low-emission: nothing greener to suggest.
LOW_EMISSION = {CommuteMode.WALK, CommuteMode.CYCLE, CommuteMode.METRO}


def indoor_exposure_cut_pct(age: int, intensity: Intensity, has_purifier: bool) -> int:
    """Percent less PM2.5 breathed by doing the activity indoors, gently, instead of outdoors.

    Indoors, play or exercise is assumed light. Without a purifier only the calmer breathing counts
    (indoor air is taken to be as dirty as outdoor); a running purifier removes about half of it.
    """
    indoor_air = INDOOR_TO_OUTDOOR.value * (1 - PURIFIER_REDUCTION.value if has_purifier else 1)
    breathed_indoors = indoor_air * inhalation_rate(age, Intensity.LIGHT)
    return round_half_up(100 * (1 - breathed_indoors / inhalation_rate(age, intensity)))


def purifier_cadr_needed(room_m2: float) -> int:
    """Clean-air delivery rate (m³/h) that gives the room 5 air changes an hour."""
    return round_half_up(room_m2 * ROOM_HEIGHT_M * PURIFIER_AIR_CHANGES_PER_HOUR)


class Alternative(StrEnum):
    METRO = "metro"
    BUS = "bus"
    CARPOOL = "carpool"


@dataclass(frozen=True)
class TransportSwap:
    current: CommuteMode
    alternative: Alternative
    weekly_km: float              # the traveller's commute distance per week
    co2_kg_saved_per_week: float
    vehicle_km_off_road_per_week: float  # fewer engines and less road dust on the city's streets


def weekly_km(commute: Commute) -> float:
    return commute.one_way_km * 2 * commute.days_per_week


def _co2_per_km(alternative: Alternative) -> float:
    if alternative is Alternative.CARPOOL:
        return CO2_PER_KM[CommuteMode.CAR].value / CARPOOL_OCCUPANCY
    return CO2_PER_KM[CommuteMode(alternative.value)].value


def _one_decimal(value: float) -> float:
    return round_half_up(value * 10) / 10


def transport_swaps(commute: Commute, city_has_metro: bool) -> list[TransportSwap]:
    """Greener ways to make the same commute, best first; empty if it's already low-emission."""
    if commute.mode in LOW_EMISSION:
        return []
    alternatives = [Alternative.METRO] if city_has_metro else []
    alternatives.append(Alternative.BUS)
    if commute.mode is CommuteMode.CAR:
        alternatives.append(Alternative.CARPOOL)

    km = weekly_km(commute)
    current_per_km = CO2_PER_KM[commute.mode].value
    swaps = []
    for alternative in alternatives:
        saved = km * (current_per_km - _co2_per_km(alternative))
        if saved <= 0:
            continue
        if commute.mode not in PRIVATE_VEHICLES:
            off_road = 0.0  # a bus rider's bus runs anyway
        elif alternative is Alternative.CARPOOL:
            off_road = km * (1 - 1 / CARPOOL_OCCUPANCY)
        else:
            off_road = km
        swaps.append(TransportSwap(commute.mode, alternative, km, _one_decimal(saved), _one_decimal(off_road)))
    return sorted(swaps, key=lambda swap: swap.co2_kg_saved_per_week, reverse=True)
