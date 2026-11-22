"""One household's plan for one day: every member's decisions, the home's actions, the commute swaps."""

from dataclasses import dataclass, replace
from datetime import date

from recyclops.domain.forecast import DayWindows, Forecast, day_windows
from recyclops.domain.home import HomeAdvice, home_actions
from recyclops.domain.household import Activity, Home, Household, Member
from recyclops.domain.impact import TransportSwap, indoor_exposure_cut_pct, transport_swaps
from recyclops.domain.rules import Action, Decision, Mask, commute_mask, decide_activity


@dataclass(frozen=True)
class CommutePlan:
    mask: Mask
    swaps: tuple[TransportSwap, ...]


@dataclass(frozen=True)
class MemberPlan:
    member: Member
    decisions: tuple[Decision, ...]
    commute: CommutePlan | None


@dataclass(frozen=True)
class DayPlan:
    day: date
    windows: DayWindows | None
    members: tuple[MemberPlan, ...]
    home: tuple[HomeAdvice, ...]


def decide(member: Member, activity: Activity, home: Home, forecast: Forecast, windows: DayWindows | None,
           day: date) -> Decision:
    """The rules' decision, plus an indoor swap's benefit, which depends on the home (is there a purifier?)."""
    decision = decide_activity(member, activity, forecast, windows, day)
    if decision.action is not Action.INDOOR:
        return decision
    cut = indoor_exposure_cut_pct(member.age, decision.activity.intensity, home.has_purifier)
    return replace(decision, exposure_cut_pct=cut)


def _member_plan(member: Member, household: Household, forecast: Forecast, windows: DayWindows | None,
                 day: date, city_has_metro: bool) -> MemberPlan:
    decisions = tuple(decide(member, activity, household.home, forecast, windows, day)
                      for activity in member.activities)
    commute = None
    if member.commute:
        commute = CommutePlan(mask=commute_mask(member.commute, forecast, day),
                              swaps=tuple(transport_swaps(member.commute, city_has_metro)))
    return MemberPlan(member, decisions, commute)


def build_plan(household: Household, forecast: Forecast, day: date, city_has_metro: bool) -> DayPlan:
    windows = day_windows(forecast, day)
    members = tuple(_member_plan(m, household, forecast, windows, day, city_has_metro) for m in household.members)
    home = tuple(home_actions(household.home, windows)) if windows else ()
    return DayPlan(day, windows, members, home)
