"""Settings, read once from the environment (and a local .env file)."""

import os
from dataclasses import dataclass, field
from datetime import timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

# India has no daylight saving, so a fixed offset is exact and needs no tz database.
IST = timezone(timedelta(hours=5, minutes=30), "Asia/Kolkata")


@dataclass(frozen=True)
class Settings:
    # repr=False keeps keys out of logs and tracebacks.
    openaq_api_key: str = field(default=os.getenv("OPENAQ_API_KEY", ""), repr=False)
    # Requests per visitor IP per minute, by route.
    air_rate_limit_per_minute: int = int(os.getenv("AIR_RATE_LIMIT_PER_MINUTE", "60"))
    plan_rate_limit_per_minute: int = int(os.getenv("PLAN_RATE_LIMIT_PER_MINUTE", "30"))
    ask_rate_limit_per_minute: int = int(os.getenv("ASK_RATE_LIMIT_PER_MINUTE", "10"))
    # A household of 5 members with their activities is a few KB; anything far bigger is not a real request.
    max_body_bytes: int = 16_000


settings = Settings()
