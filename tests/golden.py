"""The spec's golden scenarios (plans/project_spec.md, G1-G3): fixed inputs on a pinned day.

Forecast values are already-corrected hourly PM2.5 in µg/m³.
"""

from datetime import date, time

from recyclops.domain.forecast import Forecast, at
from recyclops.domain.household import (
    Activity,
    ActivityKind,
    Commute,
    CommuteMode,
    CookingFuel,
    HealthFlag,
    Home,
    Household,
    Intensity,
    Member,
    MemberType,
)

DAY = date(2026, 11, 25)  # a Wednesday


def forecast(default: float, **by_hours: float) -> Forecast:
    """A day's forecast: `default` everywhere, then values for hour ranges, e.g. h06_09=220 for 06:00-09:59."""
    hourly = {hour: default for hour in range(24)}
    for key, value in by_hours.items():
        first, last = (int(part) for part in key[1:].split("_"))
        hourly.update({hour: value for hour in range(first, last + 1)})
    return Forecast({at(DAY, time(hour)): value for hour, value in hourly.items()})


# G1 Delhi family, Very Poor. Best window 13:00-15:00, worst 20:00-22:00.
G1_FORECAST = forecast(240, h06_09=220, h10_12=150, h13_14=105, h15_16=160, h17_19=230, h20_21=240)
G1_CHILD = Member(id="aarav", name="Aarav", type=MemberType.CHILD, age=8, activities=(
    Activity(kind=ActivityKind.PLAY, start=time(17), duration_min=60, intensity=Intensity.MODERATE),))
G1_GRANDMOTHER = Member(
    id="dadi", name="Dadi", type=MemberType.SENIOR, age=68, health_flags=frozenset({HealthFlag.RESPIRATORY}),
    activities=(Activity(kind=ActivityKind.WALK, start=time(7), duration_min=30, intensity=Intensity.LIGHT),))
G1_PARENT = Member(id="priya", name="Priya", type=MemberType.ADULT, age=38, commute=Commute(
    mode=CommuteMode.CAR, one_way_km=15, days_per_week=5, departs=time(8, 30)))
G1_HOUSEHOLD = Household(
    home=Home(has_purifier=False, cooking_fuel=CookingFuel.LPG, faces_main_road=True),
    members=(G1_CHILD, G1_GRANDMOTHER, G1_PARENT))

# G2 Mumbai senior, Moderate. Best window 10:00-12:00.
G2_FORECAST = forecast(55, h06_07=70, h08_09=55, h10_11=40)
G2_SENIOR = Member(
    id="nana", name="Nana", type=MemberType.SENIOR, age=70, health_flags=frozenset({HealthFlag.HEART}),
    activities=(Activity(kind=ActivityKind.WALK, start=time(6, 30), duration_min=30, intensity=Intensity.LIGHT),))

# G3 Kolkata student commuter, Poor. Best window 12:00-14:00, worst 17:00-19:00.
G3_FORECAST = forecast(110, h08_09=110, h12_13=85, h17_18=140)
G3_STUDENT = Member(
    id="rohan", name="Rohan", type=MemberType.STUDENT, age=19,
    activities=(Activity(kind=ActivityKind.SPORT, start=time(17), duration_min=90, intensity=Intensity.HIGH),),
    commute=Commute(mode=CommuteMode.BUS, one_way_km=10, days_per_week=5, departs=time(8, 30), walking_leg_min=15))
