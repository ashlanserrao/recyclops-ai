"""What routes receive via Depends(): swapped for fakes in tests through app.dependency_overrides."""

from datetime import date, datetime

from recyclops.core.config import IST
from recyclops.data.models import AirProvider, NotConfiguredProvider

_air_provider: AirProvider = NotConfiguredProvider()


def get_air_provider() -> AirProvider:
    return _air_provider


def today_in_india() -> date:
    return datetime.now(IST).date()
