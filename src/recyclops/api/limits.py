"""One rate limiter per API route, keyed by visitor IP."""

from recyclops.core.config import settings
from recyclops.core.rate_limit import RateLimiter

RATE_LIMITERS: dict[str, RateLimiter] = {
    "/api/air": RateLimiter(settings.air_rate_limit_per_minute),
    "/api/plan": RateLimiter(settings.plan_rate_limit_per_minute),
    "/api/ask": RateLimiter(settings.ask_rate_limit_per_minute),
}
