"""The guard every request passes: body size, rate limits and security headers."""

from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import Response

from recyclops.api.errors import error_response
from recyclops.api.limits import RATE_LIMITERS
from recyclops.api.security import HSTS, SECURITY_HEADERS
from recyclops.core.config import settings


def _rejection(request: Request) -> Response | None:
    """The error response for a request that must not reach a route, or None to let it through."""
    if not request.url.path.startswith("/api/"):
        return None
    content_length = request.headers.get("content-length")
    if request.method == "POST" and not content_length:
        # Requiring a declared length stops chunked bodies from slipping past the size cap.
        return error_response(411, "Request must include a Content-Length header.")
    if content_length and (not content_length.isdigit() or int(content_length) > settings.max_body_bytes):
        return error_response(413, "Request is too large.")
    # Behind Render's proxy this is the visitor's IP because uvicorn runs with --proxy-headers (render.yaml).
    limiter = RATE_LIMITERS.get(request.url.path)
    if limiter and not limiter.allow(request.client.host if request.client else "unknown"):
        return error_response(429, "Too many requests. Please wait a minute and try again.")
    return None


async def guard_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    response = _rejection(request) or await call_next(request)
    response.headers.update(SECURITY_HEADERS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = HSTS
    return response
