"""What routes receive via Depends(): swapped for fakes in tests through app.dependency_overrides."""

from datetime import date, datetime

import httpx

from recyclops.ai.ask import QuestionReader
from recyclops.ai.chain import StructuredAI
from recyclops.ai.explain import PlanExplainer
from recyclops.core.config import IST, Settings, settings
from recyclops.data.live import LiveAirProvider
from recyclops.data.models import AirProvider, NotConfiguredProvider
from recyclops.data.open_meteo import OpenMeteo
from recyclops.data.openaq import OpenAQ


def live_air_provider(config: Settings) -> AirProvider:
    """Live data when the OpenAQ key is set; otherwise every plan says live data isn't available."""
    if not config.openaq_api_key:
        return NotConfiguredProvider()
    # One pooled client for both sources, so repeat calls reuse their connections.
    client = httpx.AsyncClient(headers={"User-Agent": "recyclops-ai"})
    return LiveAirProvider(OpenAQ(client, config.openaq_api_key), OpenMeteo(client))


# One provider for the app: its caches and last good readings are shared by every request.
_air_provider = live_air_provider(settings)
# One chain for the app: its cache, hourly cap and 429 cooldowns are shared by every request.
ai = StructuredAI(settings)
_explainer = PlanExplainer(ai)
_question_reader = QuestionReader(ai)


def get_air_provider() -> AirProvider:
    return _air_provider


def get_explainer() -> PlanExplainer:
    return _explainer


def get_question_reader() -> QuestionReader:
    return _question_reader


def today_in_india() -> date:
    return datetime.now(IST).date()
