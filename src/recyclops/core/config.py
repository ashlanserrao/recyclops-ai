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
    # AI explanations: Groq first when its key is set, OpenAI as the backup. Neither: templates only.
    groq_api_key: str = field(default=os.getenv("GROQ_API_KEY", ""), repr=False)
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    groq_reasoning_effort: str = os.getenv("GROQ_REASONING_EFFORT", "low")
    # Groq's share of the time budget: short, so a slow reply leaves the backup time to answer.
    groq_timeout_seconds: float = float(os.getenv("GROQ_TIMEOUT_SECONDS", "5"))
    openai_api_key: str = field(default=os.getenv("OPENAI_API_KEY", ""), repr=False)
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-nano")
    openai_reasoning_effort: str = os.getenv("OPENAI_REASONING_EFFORT", "minimal")
    # The whole time one AI call may take, backup included; past it the templates answer.
    ai_timeout_seconds: float = float(os.getenv("AI_TIMEOUT_SECONDS", "12"))
    # AI calls per hour from all visitors together: caps spend however many IPs arrive.
    ai_total_limit_per_hour: int = int(os.getenv("AI_TOTAL_LIMIT_PER_HOUR", "200"))
    # Requests per visitor IP per minute, by route.
    air_rate_limit_per_minute: int = int(os.getenv("AIR_RATE_LIMIT_PER_MINUTE", "60"))
    plan_rate_limit_per_minute: int = int(os.getenv("PLAN_RATE_LIMIT_PER_MINUTE", "30"))
    ask_rate_limit_per_minute: int = int(os.getenv("ASK_RATE_LIMIT_PER_MINUTE", "10"))
    # A household of 5 members with their activities is a few KB; anything far bigger is not a real request.
    max_body_bytes: int = 16_000


settings = Settings()
