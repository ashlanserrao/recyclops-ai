"""Open-Meteo's air-quality API: the modelled hourly PM2.5 forecast (CAMS global) for today and tomorrow. No key."""

from datetime import datetime

import httpx
from pydantic import BaseModel

from recyclops.core.config import IST

URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
SOURCE = "Open-Meteo (CAMS)"


class _Hourly(BaseModel):
    time: list[str]               # local (IST) hour starts, e.g. "2026-11-25T13:00"
    pm2_5: list[float | None]


class _Reply(BaseModel):
    hourly: _Hourly


class OpenMeteo:
    def __init__(self, client: httpx.AsyncClient, timeout: float = 8.0) -> None:
        self.client = client
        self.timeout = timeout

    async def modelled_pm25(self, lat: float, lon: float) -> dict[datetime, float]:
        """PM2.5 (µg/m³) keyed by the start of each hour, IST. Raises httpx.HTTPError or ValueError."""
        response = await self.client.get(URL, timeout=self.timeout, params={
            "latitude": lat, "longitude": lon, "hourly": "pm2_5", "timezone": "Asia/Kolkata",
            "forecast_days": 2, "domains": "cams_global",
        })
        response.raise_for_status()
        hourly = _Reply.model_validate_json(response.content).hourly
        return {datetime.fromisoformat(hour).replace(tzinfo=IST): value
                for hour, value in zip(hourly.time, hourly.pm2_5, strict=True) if value is not None and value >= 0}
