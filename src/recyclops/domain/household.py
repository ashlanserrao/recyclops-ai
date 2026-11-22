"""The household a plan is made for, as the browser sends it (nothing is stored on the server).

These models are also the API's request bodies: unknown fields are rejected and every value is bounded.
"""

from datetime import time
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

CHILD_UNDER = 12   # CPCB health advisories single out children and the elderly as sensitive groups
SENIOR_FROM = 60


class MemberType(StrEnum):
    CHILD = "child"
    ADULT = "adult"
    SENIOR = "senior"
    STUDENT = "student"


class HealthFlag(StrEnum):
    RESPIRATORY = "respiratory"  # asthma, COPD and similar
    HEART = "heart"
    PREGNANCY = "pregnancy"


class Intensity(StrEnum):
    LIGHT = "light"
    MODERATE = "moderate"
    HIGH = "high"


class ActivityKind(StrEnum):
    WALK = "walk"
    PLAY = "play"
    SPORT = "sport"
    EXERCISE = "exercise"
    ERRAND = "errand"
    OTHER = "other"


class CommuteMode(StrEnum):
    CAR = "car"
    TWO_WHEELER = "two_wheeler"
    AUTO = "auto"
    BUS = "bus"
    METRO = "metro"
    WALK = "walk"
    CYCLE = "cycle"


class CookingFuel(StrEnum):
    LPG = "lpg"
    PNG = "png"
    ELECTRIC = "electric"
    BIOMASS = "biomass"  # wood, dung, coal, kerosene


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Activity(_Model):
    """Something a member usually does outdoors on a given day."""
    kind: ActivityKind
    start: time
    duration_min: int = Field(ge=10, le=240)
    intensity: Intensity

    @model_validator(mode="after")
    def _ends_same_day(self) -> "Activity":
        if self.start.hour * 60 + self.start.minute + self.duration_min > 24 * 60:
            raise ValueError("An activity must end by midnight.")
        return self


class Commute(_Model):
    mode: CommuteMode
    one_way_km: float = Field(gt=0, le=100)
    days_per_week: int = Field(ge=1, le=7)
    departs: time
    walking_leg_min: int = Field(default=0, ge=0, le=60)  # walking to and from stops, each way


class Member(_Model):
    id: Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]{1,20}$")]
    # Shown to the user and passed to the AI as untrusted text (fenced, markup stripped).
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
    type: MemberType
    age: int = Field(ge=0, le=110)
    health_flags: frozenset[HealthFlag] = frozenset()
    activities: tuple[Activity, ...] = Field(default=(), max_length=5)
    commute: Commute | None = None

    @property
    def is_sensitive(self) -> bool:
        """A child, a senior or anyone with a health condition: advised more cautiously."""
        return self.age < CHILD_UNDER or self.age >= SENIOR_FROM or bool(self.health_flags)

    @property
    def is_vulnerable(self) -> bool:
        """A senior or anyone with a health condition: at Very Poor and above they stay indoors."""
        return self.age >= SENIOR_FROM or bool(self.health_flags)


class Home(_Model):
    has_purifier: bool
    purifier_room_m2: float | None = Field(default=None, gt=0, le=200)
    cooking_fuel: CookingFuel
    faces_main_road: bool


class Household(_Model):
    home: Home
    members: tuple[Member, ...] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def _unique_member_ids(self) -> "Household":
        ids = [member.id for member in self.members]
        if len(ids) != len(set(ids)):
            raise ValueError("Each member needs a different id.")
        return self
