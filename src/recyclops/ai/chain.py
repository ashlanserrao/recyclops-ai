"""The one way to the AI: a structured call that tries each provider in turn, within one time budget.

A provider that times out, errors, or replies with something that fails validation hands over to the
next. If none answers, the call returns None, and every caller has a template path for that. Repeats
come from a cache. Prompts, replies and keys are never logged: one line per attempt with the
provider, the time taken and a one-word outcome.
"""

import asyncio
import hashlib
import logging
import time
from collections.abc import Callable
from typing import Any

from openai import APITimeoutError, AuthenticationError, BadRequestError, OpenAIError, RateLimitError
from pydantic import BaseModel, ValidationError

from recyclops.ai.providers import Provider, default_providers
from recyclops.core.cache import TTLCache
from recyclops.core.config import Settings
from recyclops.core.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

# A backup with less time left than this would only time out too.
MIN_BACKUP_SECONDS = 2.0
# After a 429 a provider rests for its retry-after time, capped here (default when not given).
MAX_REST_SECONDS = 60.0
DEFAULT_REST_SECONDS = 10.0


class StructuredAI:
    def __init__(self, settings: Settings, providers: list[Provider] | None = None,
                 hourly_cap: RateLimiter | None = None) -> None:
        self.settings = settings
        self.providers = default_providers(settings) if providers is None else providers
        self.hourly_cap = hourly_cap or RateLimiter(settings.ai_total_limit_per_hour, window=3600)
        self._cache: TTLCache[BaseModel] = TTLCache()

    async def call[M: BaseModel](
        self, *, task: str, instructions: str, prompt_input: str, output: type[M], max_output_tokens: int,
        check: Callable[[M], None] | None = None,
    ) -> M | None:
        """One reply that validates as `output` (and passes `check`, which raises ValueError), or None."""
        if not self.providers:
            return None
        key = hashlib.sha256(f"{task}\n{instructions}\n{prompt_input}".encode()).hexdigest()
        if (cached := self._cache.get(key)) is not None and isinstance(cached, output):
            return cached
        if not self.hourly_cap.allow("all"):
            logger.warning("AI %s: hourly cap reached, using templates", task)
            return None

        schema = strict_schema(output)
        deadline = time.monotonic() + self.settings.ai_timeout_seconds
        for index, provider in enumerate(self.providers):
            started = time.monotonic()
            if provider.resting_until > started:
                continue
            remaining = deadline - started
            if index and remaining < MIN_BACKUP_SECONDS:
                break
            timeout = min(provider.timeout, remaining)
            try:
                text = await asyncio.wait_for(provider.reply(
                    instructions=instructions, prompt_input=prompt_input, schema=schema,
                    max_output_tokens=max_output_tokens, timeout=timeout), timeout)
                result = output.model_validate_json(text)
                if check:
                    check(result)
            except (OpenAIError, ValidationError, ValueError, TimeoutError) as exc:
                if isinstance(exc, RateLimitError):
                    provider.resting_until = time.monotonic() + _rest_seconds(exc)
                _log(task, provider, started, _failure(exc))
                continue
            _log(task, provider, started, "ok")
            self._cache.set(key, result)
            return result
        return None


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    """The model's JSON schema in the strict form both providers require: every object closed, every field required."""
    schema = model.model_json_schema()

    def close(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            for value in node.values():
                close(value)
        elif isinstance(node, list):
            for value in node:
                close(value)

    close(schema)
    return schema


def _log(task: str, provider: Provider, started: float, outcome: str) -> None:
    ms = round((time.monotonic() - started) * 1000)
    logger.info("AI %s: %s %s %s in %d ms", task, provider.name, provider.model, outcome, ms)


def _failure(exc: Exception) -> str:
    """Why an attempt failed, in one word: never the prompt (personal data), the reply or the key."""
    if isinstance(exc, (TimeoutError, APITimeoutError)):
        return "timeout"
    if isinstance(exc, RateLimitError):
        return "429"
    if isinstance(exc, AuthenticationError):
        return "auth"
    if isinstance(exc, BadRequestError):
        return "bad_request"
    if isinstance(exc, (ValidationError, ValueError)):
        return "invalid_reply"
    return "api_error"


def _rest_seconds(exc: RateLimitError) -> float:
    try:
        return min(float(exc.response.headers.get("retry-after", DEFAULT_REST_SECONDS)), MAX_REST_SECONDS)
    except ValueError:
        return DEFAULT_REST_SECONDS
