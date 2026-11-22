"""The API's request and response shapes, and how domain results map onto them."""

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from recyclops.ai.explain import Explanations, decision_key, home_key, swap_key
from recyclops.ai.templates import decision_impact, home_impact, swap_impact
from recyclops.data.models import AirSnapshot, DataStatus
from recyclops.domain.aqi import Band, Pollutant
from recyclops.domain.cities import City
from recyclops.domain.factors import EPA_EFH, IGHGP_RAIL, IGHGP_ROAD, PURIFIER_REDUCTION
from recyclops.domain.forecast import Window
from recyclops.domain.home import HomeAction, HomeAdvice
from recyclops.domain.household import Activity, Home, Household
from recyclops.domain.impact import Alternative, TransportSwap
from recyclops.domain.plan import DayPlan, MemberPlan
from recyclops.domain.rounding import round_half_up
from recyclops.domain.rules import Action, Decision, Mask, Reason

FACTOR_SOURCES = (IGHGP_ROAD, IGHGP_RAIL, EPA_EFH, PURIFIER_REDUCTION.source)


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _Out(BaseModel):
    # Fields with defaults are still always sent, so the schema (and the frontend's generated types) mark them required.
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)


class Location(_In):
    # India's mainland and islands, roughly: a guard against swapped or nonsense coordinates.
    lat: Annotated[float, Field(ge=6.0, le=37.6)]
    lon: Annotated[float, Field(ge=68.0, le=97.5)]


class PlanRequest(_In):
    location: Location
    household: Household


class AskForm(_In):
    """The question as a form: used when the AI isn't available or couldn't read the typed question."""
    member_id: str
    day: Literal["today", "tomorrow"] = "today"
    activity: Activity


class AskRequest(_In):
    location: Location
    household: Household
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)] | None = None
    form: AskForm | None = None

    @model_validator(mode="after")
    def _question_or_form(self) -> "AskRequest":
        if (self.question is None) == (self.form is None):
            raise ValueError("Send either a question or the form, not both.")
        if self.form and self.form.member_id not in {m.id for m in self.household.members}:
            raise ValueError("The form names a member who isn't in the household.")
        return self


class CityOut(_Out):
    name: str
    state: str
    lat: float
    lon: float
    has_metro: bool

    @classmethod
    def of(cls, city: City) -> "CityOut":
        return cls(name=city.name, state=city.state, lat=city.lat, lon=city.lon, has_metro=city.has_metro)


class StationOut(_Out):
    name: str
    distance_km: float


class AqiOut(_Out):
    value: int
    band: Band
    prominent: Pollutant
    method: str = "NAQI method, PM-based (24-hour averages of PM2.5 and PM10)"


class AirOut(_Out):
    status: DataStatus
    station: StationOut | None
    aqi: AqiOut | None
    pm25_24h: float | None
    pm10_24h: float | None
    measured_at: datetime | None
    source: str | None
    forecast_source: str
    forecast_corrected: bool  # scaled to the live reading, or the raw model

    @classmethod
    def of(cls, snapshot: AirSnapshot) -> "AirOut":
        reading = snapshot.reading
        aqi = reading.aqi if reading else None
        return cls(
            status=snapshot.status,
            station=StationOut(name=reading.station.name, distance_km=round(reading.station.distance_km, 1))
            if reading else None,
            aqi=AqiOut(value=aqi.value, band=aqi.band, prominent=aqi.prominent) if aqi else None,
            pm25_24h=round(reading.pm25_24h.value, 1) if reading and reading.pm25_24h else None,
            pm10_24h=round(reading.pm10_24h.value, 1) if reading and reading.pm10_24h else None,
            measured_at=reading.measured_at if reading else None,
            source=reading.source if reading else None,
            forecast_source=snapshot.forecast_source,
            forecast_corrected=snapshot.forecast.bias is not None,
        )


class WindowOut(_Out):
    start: datetime
    end: datetime
    pm25: int
    band: Band

    @classmethod
    def of(cls, window: Window) -> "WindowOut":
        return cls(start=window.start, end=window.end, pm25=round_half_up(window.mean_pm25), band=window.band)


class WindowsOut(_Out):
    best: WindowOut
    worst: WindowOut
    note: str = "From the hourly forecast: an indication, not an official AQI."


class DecisionOut(_Out):
    activity: Activity
    action: Action
    band_now: Band | None
    new_start: datetime | None
    new_duration_min: int | None
    mask: Mask
    exposure_cut_pct: int | None
    reasons: list[Reason]
    why: str               # the reasoning, in words (AI-personalised or template)
    impact: str | None     # the numbers, in words (always from code)

    @classmethod
    def of(cls, d: Decision, why: str, has_purifier: bool) -> "DecisionOut":
        return cls(activity=d.activity, action=d.action, band_now=d.band_now, new_start=d.new_start,
                   new_duration_min=d.new_duration_min, mask=d.mask, exposure_cut_pct=d.exposure_cut_pct,
                   reasons=list(d.reasons), why=why, impact=decision_impact(d, has_purifier))


class SwapOut(_Out):
    alternative: Alternative
    weekly_km: float
    co2_kg_saved_per_week: float
    vehicle_km_off_road_per_week: float
    why: str
    impact: str

    @classmethod
    def of(cls, s: TransportSwap, why: str) -> "SwapOut":
        return cls(alternative=s.alternative, weekly_km=s.weekly_km, co2_kg_saved_per_week=s.co2_kg_saved_per_week,
                   vehicle_km_off_road_per_week=s.vehicle_km_off_road_per_week, why=why, impact=swap_impact(s))


class CommuteOut(_Out):
    mask: Mask
    swaps: list[SwapOut]


class MemberPlanOut(_Out):
    member_id: str
    name: str
    decisions: list[DecisionOut]
    commute: CommuteOut | None

    @classmethod
    def of(cls, p: MemberPlan, whys: dict[str, str], has_purifier: bool) -> "MemberPlanOut":
        member_id = p.member.id
        commute = CommuteOut(mask=p.commute.mask, swaps=[
            SwapOut.of(s, whys[swap_key(member_id, s.alternative)]) for s in p.commute.swaps]) if p.commute else None
        decisions = [DecisionOut.of(d, whys[decision_key(member_id, i)], has_purifier)
                     for i, d in enumerate(p.decisions)]
        return cls(member_id=member_id, name=p.member.name, decisions=decisions, commute=commute)


class HomeAdviceOut(_Out):
    action: HomeAction
    at: datetime | None
    indoor_pm_cut_pct: int | None
    purifier_cadr_m3h: int | None
    why: str
    impact: str | None

    @classmethod
    def of(cls, a: HomeAdvice, why: str, home: Home) -> "HomeAdviceOut":
        return cls(action=a.action, at=a.at, indoor_pm_cut_pct=a.indoor_pm_cut_pct,
                   purifier_cadr_m3h=a.purifier_cadr_m3h, why=why, impact=home_impact(a, home))


class Verdict(StrEnum):
    YES = "yes"
    BETTER_TIME = "better_time"
    SHORTER = "shorter"
    INDOORS = "indoors"
    UNKNOWN = "unknown"


VERDICTS = {Action.KEEP: Verdict.YES, Action.MOVE: Verdict.BETTER_TIME, Action.SHORTEN: Verdict.SHORTER,
            Action.INDOOR: Verdict.INDOORS, Action.NO_DATA: Verdict.UNKNOWN}


class AskedOut(_Out):
    """What the app understood the question to be: shown back, so a misreading is visible."""
    member_id: str
    name: str
    day: date
    activity: Activity


class AskOut(_Out):
    air: AirOut
    needs_form: bool   # the question couldn't be read: show the form
    ai_used: bool      # the AI read the question (the decision is always code's)
    asked: AskedOut | None = None
    verdict: Verdict | None = None
    decision: DecisionOut | None = None


class PlanOut(_Out):
    city: str | None
    day: date
    air: AirOut
    windows: WindowsOut | None
    members: list[MemberPlanOut]
    home: list[HomeAdviceOut]
    ai_used: bool  # False: the explanations are the app's own templates
    sources: list[str] = Field(default_factory=lambda: list(FACTOR_SOURCES))

    @classmethod
    def of(cls, plan: DayPlan, snapshot: AirSnapshot, city: City | None, home: Home,
           explanations: Explanations) -> "PlanOut":
        whys = explanations.whys
        windows = WindowsOut(best=WindowOut.of(plan.windows.best), worst=WindowOut.of(plan.windows.worst)) \
            if plan.windows else None
        return cls(
            city=city.name if city else None, day=plan.day, air=AirOut.of(snapshot), windows=windows,
            members=[MemberPlanOut.of(m, whys, home.has_purifier) for m in plan.members],
            home=[HomeAdviceOut.of(a, whys[home_key(a.action)], home) for a in plan.home],
            ai_used=explanations.ai_used)
