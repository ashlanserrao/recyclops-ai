"""What each member should do about each outdoor activity, given the hourly forecast.

The decision table (plans/project_spec.md, "Outdoor activity decision") in code. It looks at the band
during the activity, the band of the day's cleanest 2-hour window, and who the member is:
- general: healthy adults and students;
- sensitive child: under 12, no health condition;
- vulnerable: 60+ or any health condition (asthma, heart, pregnancy).
"""

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum

from recyclops.domain.aqi import Band
from recyclops.domain.forecast import DayWindows, Forecast, at, hourly_band
from recyclops.domain.household import (
    CHILD_UNDER,
    SENIOR_FROM,
    Activity,
    Commute,
    CommuteMode,
    HealthFlag,
    Intensity,
    Member,
)
from recyclops.domain.rounding import round_half_up

BAND_ORDER = list(Band)
VULNERABLE_SHORTEN_TO_MIN = 20
SHORTEN_TO_MIN = 30
# Modes where the commuter breathes street air directly.
OPEN_AIR_MODES = {CommuteMode.WALK, CommuteMode.CYCLE, CommuteMode.TWO_WHEELER, CommuteMode.AUTO}


class Action(StrEnum):
    KEEP = "keep"
    MOVE = "move"          # to the day's cleanest window
    SHORTEN = "shorten"    # same time, less of it
    INDOOR = "indoor"      # swap for an indoor alternative
    NO_DATA = "no_data"    # the forecast doesn't cover this time


class Mask(StrEnum):
    NONE = "none"
    N95 = "n95"


class Reason(StrEnum):
    """Why a decision was made: the AI and the templates explain these, they never invent their own."""
    AIR_OK = "air_ok"
    SEVERE_AIR = "severe_air"
    CLEANER_WINDOW = "cleaner_window"
    NO_CLEANER_WINDOW = "no_cleaner_window"
    HIGH_INTENSITY = "high_intensity"      # hard exercise means breathing far more air
    LIGHT_ONLY = "light_only"
    AVOID_MAIN_ROAD = "avoid_main_road"    # traffic-side air is dirtier than the station average
    SENSITIVE_CHILD = "sensitive_child"
    SENSITIVE_SENIOR = "sensitive_senior"
    HEALTH_RESPIRATORY = "health_respiratory"
    HEALTH_HEART = "health_heart"
    HEALTH_PREGNANCY = "health_pregnancy"
    NO_FORECAST = "no_forecast"


_HEALTH_REASONS = {
    HealthFlag.RESPIRATORY: Reason.HEALTH_RESPIRATORY,
    HealthFlag.HEART: Reason.HEALTH_HEART,
    HealthFlag.PREGNANCY: Reason.HEALTH_PREGNANCY,
}


@dataclass(frozen=True)
class Decision:
    member_id: str
    activity: Activity
    action: Action
    reasons: tuple[Reason, ...]
    band_now: Band | None = None
    new_start: datetime | None = None
    new_duration_min: int | None = None
    mask: Mask = Mask.NONE
    exposure_cut_pct: int | None = None  # less PM2.5 breathed in than the original plan


def _rank(band: Band) -> int:
    return BAND_ORDER.index(band)


def _unique(reasons: list[Reason]) -> tuple[Reason, ...]:
    """In first-seen order, each reason once."""
    return tuple(dict.fromkeys(reasons))


def _personal_reasons(member: Member) -> list[Reason]:
    """Who the member is, as far as the advice is concerned: age group first, then health conditions."""
    age_group = []
    if member.age >= SENIOR_FROM:
        age_group = [Reason.SENSITIVE_SENIOR]
    elif member.age < CHILD_UNDER:
        age_group = [Reason.SENSITIVE_CHILD]
    return age_group + [_HEALTH_REASONS[flag] for flag in HealthFlag if flag in member.health_flags]


def _exposure_cut(old_pm25: float, old_minutes: int, new_pm25: float, new_minutes: int) -> int:
    """Percent less PM2.5 inhaled: concentration × time, same breathing rate on both sides (conservative)."""
    return round_half_up(100 * (1 - (new_pm25 * new_minutes) / (old_pm25 * old_minutes)))


@dataclass(frozen=True)
class _Situation:
    member: Member
    activity: Activity
    start: datetime
    pm25_now: float
    band_now: Band
    windows: DayWindows
    forecast: Forecast

    def decision(self, action: Action, reasons: list[Reason], *, new_start: datetime | None = None,
                 new_duration_min: int | None = None, mask: Mask = Mask.NONE,
                 exposure_cut_pct: int | None = None) -> Decision:
        return Decision(self.member.id, self.activity, action, _unique(reasons), self.band_now,
                        new_start, new_duration_min, mask, exposure_cut_pct)

    def move(self, reasons: list[Reason], worst_allowed: Band, cap_min: int | None = None) -> Decision | None:
        """Move to the cleanest window if it's at most `worst_allowed` and actually cleaner; else None."""
        best = self.windows.best
        minutes = min(self.activity.duration_min, cap_min) if cap_min else self.activity.duration_min
        new_pm25 = self.forecast.mean_over(best.start, minutes)
        if _rank(best.band) > _rank(worst_allowed) or new_pm25 is None or new_pm25 >= self.pm25_now:
            return None
        return self.decision(
            Action.MOVE, [*reasons, Reason.CLEANER_WINDOW], new_start=best.start, new_duration_min=minutes,
            exposure_cut_pct=_exposure_cut(self.pm25_now, self.activity.duration_min, new_pm25, minutes))

    def shorten(self, reasons: list[Reason], cap_min: int, mask: Mask = Mask.NONE) -> Decision:
        if self.activity.duration_min <= cap_min:  # already short enough
            return self.decision(Action.KEEP, [*reasons, Reason.NO_CLEANER_WINDOW], mask=mask)
        return self.decision(
            Action.SHORTEN, [*reasons, Reason.NO_CLEANER_WINDOW], new_duration_min=cap_min, mask=mask,
            exposure_cut_pct=_exposure_cut(self.pm25_now, self.activity.duration_min, self.pm25_now, cap_min))

    def indoor(self, reasons: list[Reason]) -> Decision:
        return self.decision(Action.INDOOR, reasons)


def decide_activity(member: Member, activity: Activity, forecast: Forecast, windows: DayWindows | None,
                    day: date) -> Decision:
    start = at(day, activity.start)
    pm25_now = forecast.mean_over(start, activity.duration_min)
    if pm25_now is None or windows is None:
        return Decision(member.id, activity, Action.NO_DATA, (Reason.NO_FORECAST,))
    situation = _Situation(member, activity, start, pm25_now, hourly_band(pm25_now), windows, forecast)
    decision = _apply_table(situation)
    stays_outdoors = decision.action in (Action.KEEP, Action.MOVE, Action.SHORTEN)
    if member.is_sensitive and stays_outdoors and _rank(situation.band_now) >= _rank(Band.MODERATE):
        decision = replace(decision, reasons=_unique([*decision.reasons, Reason.AVOID_MAIN_ROAD]))
    return decision


def _apply_table(s: _Situation) -> Decision:
    member, band = s.member, s.band_now
    personal = _personal_reasons(member)
    high = s.activity.intensity is Intensity.HIGH
    effort = [Reason.HIGH_INTENSITY] if high else []
    gentle = [] if s.activity.intensity is Intensity.LIGHT else [Reason.LIGHT_ONLY]

    if _rank(band) <= _rank(Band.SATISFACTORY):
        return s.decision(Action.KEEP, [Reason.AIR_OK])
    if band is Band.SEVERE:
        return s.indoor([Reason.SEVERE_AIR, *personal])

    if band is Band.MODERATE:
        if member.is_vulnerable:
            return s.move(personal, Band.SATISFACTORY) or s.shorten(personal, VULNERABLE_SHORTEN_TO_MIN)
        if member.is_sensitive:
            return s.decision(Action.KEEP, [*personal, *gentle])
        if high and (moved := s.move(effort, Band.SATISFACTORY)):
            return moved
        return s.decision(Action.KEEP, effort)

    if band is Band.POOR:
        if member.is_sensitive:
            return s.move([*personal, *gentle], Band.MODERATE, SHORTEN_TO_MIN) or s.indoor(personal)
        return s.move(effort, Band.MODERATE) or s.shorten(effort, SHORTEN_TO_MIN)

    # Very Poor
    if member.is_vulnerable:
        return s.indoor(personal)
    if member.is_sensitive:
        return s.move([*personal, *gentle], Band.POOR, SHORTEN_TO_MIN) or s.indoor(personal)
    if moved := s.move(effort, Band.MODERATE):
        return moved
    return s.indoor(effort) if high else s.shorten(effort, SHORTEN_TO_MIN, Mask.N95)


def commute_mask(commute: Commute, forecast: Forecast, day: date) -> Mask:
    """An N95 when the commute breathes street air (open mode or a walking leg) at Poor or worse."""
    if commute.mode not in OPEN_AIR_MODES and commute.walking_leg_min == 0:
        return Mask.NONE
    pm25 = forecast.mean_over(at(day, commute.departs), max(commute.walking_leg_min, 10))
    if pm25 is None:
        return Mask.NONE
    return Mask.N95 if _rank(hourly_band(pm25)) >= _rank(Band.POOR) else Mask.NONE
