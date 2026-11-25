"""Every error leaves as plain-language JSON, {"error": ..., "fields": [...]}, never echoing input or internals."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from recyclops.data.models import LiveDataUnavailableError

logger = logging.getLogger(__name__)


def error_response(status: int, message: str, fields: list[dict[str, str]] | None = None) -> JSONResponse:
    body: dict[str, Any] = {"error": message}
    if fields:
        body["fields"] = fields
    return JSONResponse(status_code=status, content=body)


def _field_errors(errors: Any) -> list[dict[str, str]]:
    """Field path and pydantic's message for each problem; the submitted value is dropped."""
    found = []
    for error in errors:
        location = tuple(str(part) for part in error.get("loc", ()) if part not in ("body", "query"))
        # Our own validators' messages are written for people; pydantic prefixes them with "Value error, ".
        found.append((location, str(error.get("msg", "Invalid value")).removeprefix("Value error, ")))
    # A failed member leaves the members list one short, and pydantic reports that too. The member's own
    # error already explains it, so an error on a field that contains another error is dropped.
    return [{"field": ".".join(location) or "request", "message": message}
            for location, message in found
            if not any(other[:len(location)] == location and other != location for other, _ in found)]


def add_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = _field_errors(exc.errors())
        logger.warning("Rejected %s: %s", request.url.path, "; ".join(f"{f['field']}: {f['message']}" for f in fields))
        return error_response(422, "Please check the highlighted fields.", fields)

    @app.exception_handler(LiveDataUnavailableError)
    async def no_live_data(_: Request, __: LiveDataUnavailableError) -> JSONResponse:
        return error_response(503, "Live air-quality data isn't available right now. Please try again later.")

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        messages = {404: "Not found.", 405: "Method not allowed."}
        return error_response(exc.status_code, messages.get(exc.status_code, "Request could not be handled."))

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return error_response(500, "Something went wrong. Please try again.")
