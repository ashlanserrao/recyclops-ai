"""The outdoor-activity decision table and commute masks (spec V7, V8), plus the golden scenarios."""

from datetime import time

import pytest

from recyclops.domain.aqi import Band
from recyclops.domain.forecast import Forecast, at, day_windows
from recyclops.domain.household import Activity, ActivityKind, Intensity, Member, MemberType
from recyclops.domain.rules import Action, Decision, Mask, Reason, commute_mask, decide_activity
from tests.golden import (
    DAY,
    G1_CHILD,
    G1_FORECAST,
    G1_GRANDMOTHER,
    G1_PARENT,
    G2_FORECAST,
    G2_SENIOR,
    G3_FORECAST,
    G3_STUDENT,
    forecast,
)

GENERAL = Member(id="adult", name="Adult", type=MemberType.ADULT, age=30)
CHILD = Member(id="child", name="Child", type=MemberType.CHILD, age=8)
VULNERABLE = Member(id="senior", name="Senior", type=MemberType.SENIOR, age=70)
LIGHT, MODERATE, HIGH = Intensity.LIGHT, Intensity.MODERATE, Intensity.HIGH
R = Reason


def decide(member: Member, now: float, elsewhere: float, intensity: Intensity = MODERATE) -> Decision:
    """An hour-long activity at 18:00 with PM2.5 `now`; every other hour of the day at `elsewhere`."""
    activity = Activity(kind=ActivityKind.PLAY, start=time(18), duration_min=60, intensity=intensity)
    day = forecast(elsewhere, h18_18=now)
    return decide_activity(member, activity, day, day_windows(day, DAY), DAY)


def golden(member: Member, day: Forecast) -> Decision:
    return decide_activity(member, member.activities[0], day, day_windows(day, DAY), DAY)


# One case per row of the decision table. PM2.5 40 Satisfactory, 75/80 Moderate, 100/110 Poor,
# 150/200 Very Poor, 300 Severe.
@pytest.mark.parametrize(("member", "now", "elsewhere", "intensity", "action", "reasons"), [
    (GENERAL, 50, 40, MODERATE, Action.KEEP, (R.AIR_OK,)),
    (GENERAL, 75, 40, LIGHT, Action.KEEP, ()),
    (GENERAL, 75, 40, HIGH, Action.MOVE, (R.HIGH_INTENSITY, R.CLEANER_WINDOW)),
    (GENERAL, 75, 70, HIGH, Action.KEEP, (R.HIGH_INTENSITY,)),
    (CHILD, 75, 40, MODERATE, Action.KEEP, (R.SENSITIVE_CHILD, R.LIGHT_ONLY, R.AVOID_MAIN_ROAD)),
    (VULNERABLE, 75, 40, LIGHT, Action.MOVE, (R.SENSITIVE_SENIOR, R.CLEANER_WINDOW, R.AVOID_MAIN_ROAD)),
    (VULNERABLE, 75, 80, LIGHT, Action.SHORTEN, (R.SENSITIVE_SENIOR, R.NO_CLEANER_WINDOW, R.AVOID_MAIN_ROAD)),
    (GENERAL, 110, 80, MODERATE, Action.MOVE, (R.CLEANER_WINDOW,)),
    (GENERAL, 110, 100, MODERATE, Action.SHORTEN, (R.NO_CLEANER_WINDOW,)),
    (CHILD, 110, 80, MODERATE, Action.MOVE,
     (R.SENSITIVE_CHILD, R.LIGHT_ONLY, R.CLEANER_WINDOW, R.AVOID_MAIN_ROAD)),
    (CHILD, 110, 100, MODERATE, Action.INDOOR, (R.SENSITIVE_CHILD,)),
    (GENERAL, 200, 80, MODERATE, Action.MOVE, (R.CLEANER_WINDOW,)),
    (GENERAL, 200, 110, HIGH, Action.INDOOR, (R.HIGH_INTENSITY,)),
    (GENERAL, 200, 110, MODERATE, Action.SHORTEN, (R.NO_CLEANER_WINDOW,)),
    (CHILD, 200, 110, MODERATE, Action.MOVE,
     (R.SENSITIVE_CHILD, R.LIGHT_ONLY, R.CLEANER_WINDOW, R.AVOID_MAIN_ROAD)),
    (CHILD, 200, 150, MODERATE, Action.INDOOR, (R.SENSITIVE_CHILD,)),
    (VULNERABLE, 200, 40, LIGHT, Action.INDOOR, (R.SENSITIVE_SENIOR,)),
    (GENERAL, 300, 40, LIGHT, Action.INDOOR, (R.SEVERE_AIR,)),
])
def test_decision_table(member: Member, now: float, elsewhere: float, intensity: Intensity, action: Action,
                        reasons: tuple[Reason, ...]) -> None:
    decision = decide(member, now, elsewhere, intensity)
    assert (decision.action, decision.reasons) == (action, reasons)


def test_sensitive_moves_are_capped_at_30_minutes() -> None:
    decision = decide(CHILD, 110, 80)
    assert (decision.new_start, decision.new_duration_min) == (at(DAY, time(6)), 30)


def test_shortening_cuts_exposure_by_the_time_saved() -> None:
    decision = decide(VULNERABLE, 75, 80, LIGHT)
    assert (decision.new_duration_min, decision.exposure_cut_pct) == (20, 67)  # 1 - 20/60


def test_very_poor_shortened_activity_needs_a_mask() -> None:
    assert decide(GENERAL, 200, 110).mask is Mask.N95


def test_no_forecast_means_no_decision() -> None:
    activity = Activity(kind=ActivityKind.WALK, start=time(7), duration_min=30, intensity=LIGHT)
    decision = decide_activity(GENERAL, activity, Forecast({}), None, DAY)
    assert (decision.action, decision.reasons) == (Action.NO_DATA, (R.NO_FORECAST,))


def test_g1_child_plays_earlier_and_shorter() -> None:
    decision = golden(G1_CHILD, G1_FORECAST)
    assert decision.band_now is Band.VERY_POOR
    assert (decision.action, decision.new_start, decision.new_duration_min, decision.exposure_cut_pct) == (
        Action.MOVE, at(DAY, time(13)), 30, 77)  # 1 - (105 × 30) / (230 × 60)
    assert R.LIGHT_ONLY in decision.reasons


def test_g1_grandmother_stays_indoors() -> None:
    decision = golden(G1_GRANDMOTHER, G1_FORECAST)
    assert (decision.action, decision.reasons) == (Action.INDOOR, (R.SENSITIVE_SENIOR, R.HEALTH_RESPIRATORY))


def test_g1_parent_drives_without_a_mask() -> None:
    assert G1_PARENT.commute is not None
    assert commute_mask(G1_PARENT.commute, G1_FORECAST, DAY) is Mask.NONE


def test_g2_senior_walks_later() -> None:
    decision = golden(G2_SENIOR, G2_FORECAST)
    assert decision.band_now is Band.MODERATE
    assert (decision.action, decision.new_start, decision.new_duration_min, decision.exposure_cut_pct) == (
        Action.MOVE, at(DAY, time(10)), 30, 43)  # 1 - 40/70
    assert {R.HEALTH_HEART, R.AVOID_MAIN_ROAD} <= set(decision.reasons)


def test_g3_student_plays_football_at_noon_and_masks_the_walk() -> None:
    decision = golden(G3_STUDENT, G3_FORECAST)
    assert (decision.action, decision.new_start, decision.new_duration_min, decision.exposure_cut_pct) == (
        Action.MOVE, at(DAY, time(12)), 90, 39)  # 1 - 85/140
    assert G3_STUDENT.commute is not None
    assert commute_mask(G3_STUDENT.commute, G3_FORECAST, DAY) is Mask.N95
