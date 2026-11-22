"""Indoor air actions for the household: active steps for the day, not passive monitoring.

There is no indoor sensor. Advice follows from the day's outdoor forecast and the home's details,
and the one number given (the purifier's effect) comes from a cited study (factors.py).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from recyclops.domain.aqi import Band
from recyclops.domain.factors import PURIFIER_REDUCTION
from recyclops.domain.forecast import DayWindows
from recyclops.domain.household import CookingFuel, Home
from recyclops.domain.impact import purifier_cadr_needed
from recyclops.domain.rounding import round_half_up

BAND_ORDER = list(Band)


class HomeAction(StrEnum):
    KEEP_WINDOWS_SHUT = "keep_windows_shut"            # through the day's worst window
    AIR_OUT_IN_BEST_WINDOW = "air_out_in_best_window"  # 10-15 minutes, for stale air and cooking fumes
    CLOSE_ROAD_SIDE = "close_road_side"                # road-facing windows stay shut; air from the back
    RUN_PURIFIER = "run_purifier"
    CONSIDER_PURIFIER = "consider_purifier"
    SWITCH_FROM_BIOMASS = "switch_from_biomass"        # wood, dung, coal or kerosene smoke indoors
    USE_KITCHEN_EXHAUST = "use_kitchen_exhaust"
    WET_MOP = "wet_mop"                                # sweeping lifts settled dust back into the air
    NO_INCENSE_OR_COILS = "no_incense_or_coils"


@dataclass(frozen=True)
class HomeAdvice:
    action: HomeAction
    at: datetime | None = None          # when, for advice tied to a window of the day
    indoor_pm_cut_pct: int | None = None
    purifier_cadr_m3h: int | None = None  # what the purifier should deliver for the stated room


def _at_least(band: Band, threshold: Band) -> bool:
    return BAND_ORDER.index(band) >= BAND_ORDER.index(threshold)


def home_actions(home: Home, windows: DayWindows) -> list[HomeAdvice]:
    worst = windows.worst.band
    polluted_day = _at_least(worst, Band.POOR)
    purifier_cut = round_half_up(100 * PURIFIER_REDUCTION.value)

    advice = []
    if polluted_day:
        advice.append(HomeAdvice(HomeAction.KEEP_WINDOWS_SHUT, at=windows.worst.start))
    advice.append(HomeAdvice(HomeAction.AIR_OUT_IN_BEST_WINDOW, at=windows.best.start))
    if home.faces_main_road and _at_least(worst, Band.MODERATE):
        advice.append(HomeAdvice(HomeAction.CLOSE_ROAD_SIDE))
    if home.has_purifier and _at_least(worst, Band.MODERATE):
        cadr = purifier_cadr_needed(home.purifier_room_m2) if home.purifier_room_m2 else None
        advice.append(HomeAdvice(HomeAction.RUN_PURIFIER, indoor_pm_cut_pct=purifier_cut, purifier_cadr_m3h=cadr))
    elif not home.has_purifier and polluted_day:
        advice.append(HomeAdvice(HomeAction.CONSIDER_PURIFIER, indoor_pm_cut_pct=purifier_cut))
    if home.cooking_fuel is CookingFuel.BIOMASS:
        advice.append(HomeAdvice(HomeAction.SWITCH_FROM_BIOMASS))
    if polluted_day:
        advice += [HomeAdvice(HomeAction.USE_KITCHEN_EXHAUST), HomeAdvice(HomeAction.WET_MOP),
                   HomeAdvice(HomeAction.NO_INCENSE_OR_COILS)]
    return advice
