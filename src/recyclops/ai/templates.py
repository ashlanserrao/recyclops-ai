"""Fixed wording for every decision: the app's own explanation when there is no AI, and the AI's draft.

Two texts per item:
- why: the reasoning, with no numbers in it (so the AI's rewrite of it can be checked for invented ones);
- impact: the numbers, always written here from the computed values, never by the AI.
"""

from datetime import datetime, timedelta

from recyclops.domain.aqi import Band
from recyclops.domain.forecast import WINDOW_HOURS
from recyclops.domain.home import HomeAction, HomeAdvice
from recyclops.domain.household import ActivityKind, Home
from recyclops.domain.impact import Alternative, TransportSwap
from recyclops.domain.rules import Action, Decision, Mask, Reason

BAND_WORDS = {
    Band.GOOD: "good", Band.SATISFACTORY: "satisfactory", Band.MODERATE: "moderate", Band.POOR: "poor",
    Band.VERY_POOR: "very poor", Band.SEVERE: "severe",
}
ACTIVITY_WORDS = {
    ActivityKind.WALK: "walk", ActivityKind.PLAY: "outdoor play", ActivityKind.SPORT: "sport",
    ActivityKind.EXERCISE: "exercise", ActivityKind.ERRAND: "errand", ActivityKind.OTHER: "outing",
}
# Why the reason matters, as the end of "This matters because ...".
_BECAUSE = {
    Reason.SENSITIVE_CHILD: "children breathe in more air for their size than adults do",
    Reason.SENSITIVE_SENIOR: "polluted air strains older lungs and hearts more",
    Reason.HEALTH_RESPIRATORY: "polluted air can trigger asthma and other breathing problems",
    Reason.HEALTH_HEART: "fine particles put extra strain on the heart",
    Reason.HEALTH_PREGNANCY: "fine particles in the air can affect a pregnancy",
    Reason.HIGH_INTENSITY: "hard exercise means breathing several times more air",
}
_EXTRA = {
    Reason.LIGHT_ONLY: "Keep it gentle, so less air is breathed in.",
    Reason.AVOID_MAIN_ROAD: "Stay away from busy roads, where the air is dirtier than at the monitoring station.",
}


def clock(moment: datetime) -> str:
    """5 pm, 6:30 am, 12 pm."""
    hour = moment.hour % 12 or 12
    suffix = "am" if moment.hour < 12 else "pm"
    return f"{hour}:{moment.minute:02d} {suffix}" if moment.minute else f"{hour} {suffix}"


def _because(reasons: tuple[Reason, ...]) -> str:
    clauses = [_BECAUSE[r] for r in reasons if r in _BECAUSE]
    return f" This matters because {' and '.join(clauses)}." if clauses else ""


def _extras(reasons: tuple[Reason, ...]) -> str:
    return "".join(f" {_EXTRA[r]}" for r in reasons if r in _EXTRA)


def decision_why(decision: Decision, best_band: Band | None) -> str:
    activity = ACTIVITY_WORDS[decision.activity.kind]
    band = BAND_WORDS[decision.band_now] if decision.band_now else ""
    reasons = decision.reasons
    match decision.action:
        case Action.NO_DATA:
            return "There is no forecast for this time yet, so no advice can be given."
        case Action.KEEP if Reason.AIR_OK in reasons:
            return f"The air will be {band} then, so the {activity} can go ahead as planned."
        case Action.KEEP:
            text = f"The air will be {band} then, which is acceptable for the {activity}."
        case Action.MOVE:
            best = BAND_WORDS[best_band] if best_band else "cleaner"
            text = (f"The air will be {band} at the planned time. The cleanest part of the day is {best}, "
                    f"so moving the {activity} there means breathing cleaner air.")
        case Action.SHORTEN:
            text = (f"The air will be {band} then and no part of the day is much cleaner, "
                    f"so a shorter {activity} means breathing less of it.")
        case Action.INDOOR if Reason.SEVERE_AIR in reasons:
            text = f"The air will be severe, which is unsafe for everyone outdoors, so do the {activity} indoors."
        case Action.INDOOR:
            text = (f"The air will be {band} then, too polluted for the {activity} outdoors; "
                    "an indoor alternative is safer.")
    return text + _because(reasons) + _extras(reasons)


def decision_impact(decision: Decision, has_purifier: bool) -> str | None:
    cut = decision.exposure_cut_pct
    mask = " Wear a well-fitted N95 mask outdoors." if decision.mask is Mask.N95 else ""
    if decision.action is Action.MOVE and decision.new_start and decision.new_duration_min:
        end = decision.new_start + timedelta(minutes=decision.new_duration_min)
        return (f"{clock(decision.new_start)} to {clock(end)}, {decision.new_duration_min} minutes: "
                f"about {cut}% less PM2.5 breathed in.{mask}")
    if decision.action is Action.SHORTEN:
        return f"Kept to {decision.new_duration_min} minutes: about {cut}% less PM2.5 breathed in.{mask}"
    if decision.action is Action.INDOOR and cut:
        purifier = " with the purifier running" if has_purifier else ""
        return f"Indoors and gentler{purifier}: about {cut}% less PM2.5 breathed in."
    if decision.action is Action.INDOOR:
        return ("Without a purifier, indoor air is about as polluted as outdoor air: staying in helps most "
                "with windows shut and a purifier running.")
    return mask.strip() or None


_HOME_WHY = {
    HomeAction.KEEP_WINDOWS_SHUT:
        "The outside air is at its worst in this stretch; closed windows keep most of it out.",
    HomeAction.AIR_OUT_IN_BEST_WINDOW:
        "Opening up briefly when the outside air is cleanest clears cooking fumes and stale air without letting "
        "the worst of the smog in.",
    HomeAction.CLOSE_ROAD_SIDE:
        "Traffic makes road-facing air the dirtiest; let air in from the side away from the road.",
    HomeAction.RUN_PURIFIER: "A purifier is the one thing that actually cleans the air indoors.",
    HomeAction.CONSIDER_PURIFIER:
        "Without a purifier, indoor air is about as polluted as outdoor air on days like this.",
    HomeAction.SWITCH_FROM_BIOMASS:
        "Smoke from wood, dung, coal or kerosene is one of the biggest sources of indoor pollution in Indian "
        "homes; LPG, PNG or electric cooking avoids it.",
    HomeAction.USE_KITCHEN_EXHAUST:
        "With windows shut, cooking fumes stay inside unless a chimney or exhaust fan carries them out.",
    HomeAction.WET_MOP: "Sweeping throws settled dust back into the air; a damp mop holds on to it.",
    HomeAction.NO_INCENSE_OR_COILS: "Incense and mosquito coils add fine smoke to air that is already polluted.",
}


def home_why(advice: HomeAdvice) -> str:
    return _HOME_WHY[advice.action]


def home_impact(advice: HomeAdvice, home: Home) -> str | None:
    match advice.action:
        case HomeAction.KEEP_WINDOWS_SHUT if advice.at:
            return f"Shut from {clock(advice.at)} to {clock(advice.at + timedelta(hours=WINDOW_HOURS))}."
        case HomeAction.AIR_OUT_IN_BEST_WINDOW if advice.at:
            return f"Open the windows for 10 to 15 minutes from {clock(advice.at)}."
        case HomeAction.RUN_PURIFIER:
            size = (f" For your {home.purifier_room_m2:g} m² room, it needs a clean-air delivery rate (CADR) of at "
                    f"least {advice.purifier_cadr_m3h} m³/h." if advice.purifier_cadr_m3h else "")
            return f"Cuts indoor PM2.5 by about {advice.indoor_pm_cut_pct}%.{size}"
        case HomeAction.CONSIDER_PURIFIER:
            return f"A purifier sized for the room cuts indoor PM2.5 by about {advice.indoor_pm_cut_pct}%."
    return None


_SWAP_WHY = {
    Alternative.METRO:
        "The metro runs on its schedule anyway, so one more rider adds very little, and the road gets one "
        "vehicle less.",
    Alternative.BUS: "A bus carries dozens of people for the fuel of a few cars.",
    Alternative.CARPOOL:
        "Sharing one car between three people cuts each person's share of its exhaust to a third.",
}


def swap_why(swap: TransportSwap) -> str:
    return _SWAP_WHY[swap.alternative]


def swap_impact(swap: TransportSwap) -> str:
    off_road = (f" and takes {swap.vehicle_km_off_road_per_week:g} km of driving off the roads"
                if swap.vehicle_km_off_road_per_week else "")
    return f"Saves about {swap.co2_kg_saved_per_week:g} kg of CO2 a week{off_road}."
