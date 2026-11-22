"""POST /api/plan: the household's plan for today, from live air data and the rules (no AI involved yet)."""

from datetime import date

from fastapi import APIRouter, Depends

from recyclops.api.dependencies import get_air_provider, today_in_india
from recyclops.api.schemas import PlanOut, PlanRequest
from recyclops.data.models import AirProvider
from recyclops.domain.cities import nearest_city
from recyclops.domain.plan import build_plan

router = APIRouter()


@router.post("/api/plan")
async def plan(
    request: PlanRequest,
    provider: AirProvider = Depends(get_air_provider),
    today: date = Depends(today_in_india),
) -> PlanOut:
    location = request.location
    snapshot = await provider.snapshot(location.lat, location.lon)
    city = nearest_city(location.lat, location.lon)
    day_plan = build_plan(request.household, snapshot.forecast, today, city_has_metro=bool(city and city.has_metro))
    return PlanOut.of(day_plan, snapshot, city)
