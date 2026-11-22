"""GET /api/cities: the cities the planner knows by name, for the location picker.

Served from the backend so the browser's list can't drift from the one plans are made with.
"""

from fastapi import APIRouter, Response

from recyclops.api.schemas import CityOut
from recyclops.domain.cities import CITIES

router = APIRouter()

_SORTED = [CityOut.of(city) for city in sorted(CITIES, key=lambda c: c.name)]


@router.get("/api/cities")
async def cities(response: Response) -> list[CityOut]:
    # A fixed list that changes only with a deploy: browsers may reuse it for a day.
    response.headers["Cache-Control"] = "public, max-age=86400"
    return _SORTED
