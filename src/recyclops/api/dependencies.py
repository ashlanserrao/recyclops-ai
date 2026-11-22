"""What routes receive via Depends(): swapped for fakes in tests through app.dependency_overrides."""

from datetime import date, datetime

from recyclops.ai.chain import StructuredAI
from recyclops.ai.explain import PlanExplainer
from recyclops.core.config import IST, settings
from recyclops.data.models import AirProvider, NotConfiguredProvider

_air_provider: AirProvider = NotConfiguredProvider()
# One chain for the app: its cache, hourly cap and 429 cooldowns are shared by every request.
ai = StructuredAI(settings)
_explainer = PlanExplainer(ai)


def get_air_provider() -> AirProvider:
    return _air_provider


def get_explainer() -> PlanExplainer:
    return _explainer


def today_in_india() -> date:
    return datetime.now(IST).date()
