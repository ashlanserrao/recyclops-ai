"""The AI providers the chain can call, each behind the same small interface.

Both speak the OpenAI SDK: Groq through its OpenAI-compatible Chat Completions endpoint, OpenAI
through its Responses API. Both are asked for a strict JSON schema.
"""

from typing import Any

from openai import AsyncOpenAI

from recyclops.core.config import Settings

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class Provider:
    name = ""

    def __init__(self, settings: Settings, client: AsyncOpenAI, timeout: float) -> None:
        self.settings = settings
        self.client = client
        self.timeout = timeout
        self.resting_until = 0.0  # monotonic time; set after a 429 so bursts skip straight to the backup

    @property
    def model(self) -> str:
        raise NotImplementedError

    async def reply(self, *, instructions: str, prompt_input: str, schema: dict[str, Any], max_output_tokens: int,
                    timeout: float) -> str:
        """The reply's text, which should be JSON matching `schema` (the caller checks)."""
        raise NotImplementedError


class GroqProvider(Provider):
    """Tried first: fast, and its Chat Completions endpoint documents strict JSON schemas."""

    name = "groq"

    @property
    def model(self) -> str:
        return self.settings.groq_model

    async def reply(self, *, instructions: str, prompt_input: str, schema: dict[str, Any], max_output_tokens: int,
                    timeout: float) -> str:
        options: dict[str, Any] = {}
        if self.settings.groq_reasoning_effort:
            options["reasoning_effort"] = self.settings.groq_reasoning_effort
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": instructions}, {"role": "user", "content": prompt_input}],
            response_format={"type": "json_schema", "json_schema": {"name": "reply", "schema": schema, "strict": True}},
            max_completion_tokens=max_output_tokens,
            extra_body={"include_reasoning": False},  # only the JSON comes back
            timeout=timeout,
            **options,
        )
        return response.choices[0].message.content or "" if response.choices else ""


class OpenAIProvider(Provider):
    """The backup. store=False: nothing is kept on OpenAI's side."""

    name = "openai"

    @property
    def model(self) -> str:
        return self.settings.openai_model

    async def reply(self, *, instructions: str, prompt_input: str, schema: dict[str, Any], max_output_tokens: int,
                    timeout: float) -> str:
        options: dict[str, Any] = {}
        if self.settings.openai_reasoning_effort:
            options["reasoning"] = {"effort": self.settings.openai_reasoning_effort}
        response = await self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt_input,
            text={"format": {"type": "json_schema", "name": "reply", "schema": schema, "strict": True}},
            max_output_tokens=max_output_tokens,
            store=False,
            timeout=timeout,
            **options,
        )
        return str(response.output_text)


def default_providers(settings: Settings) -> list[Provider]:
    """The chain the keys allow: Groq, then OpenAI. Empty when neither key is set (templates only)."""
    providers: list[Provider] = []
    if settings.groq_api_key:
        client = AsyncOpenAI(api_key=settings.groq_api_key, base_url=GROQ_BASE_URL, max_retries=0)
        providers.append(GroqProvider(settings, client, settings.groq_timeout_seconds))
    if settings.openai_api_key:
        client = AsyncOpenAI(api_key=settings.openai_api_key, max_retries=0)
        providers.append(OpenAIProvider(settings, client, settings.ai_timeout_seconds))
    return providers
