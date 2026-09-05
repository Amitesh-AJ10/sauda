import json
import os
import time
from typing import TypeVar

from groq import Groq
from pydantic import BaseModel

from app.observability.tracing import get_tracer

# gpt-oss is a reasoning model too, but (unlike qwen3 on Groq) accepts
# `reasoning_effort` to keep its hidden chain-of-thought short — that's what
# was blowing past Groq's free-tier output-token-per-minute cap on qwen3.
DEFAULT_MODEL = "openai/gpt-oss-20b"
MAX_OUTPUT_TOKENS = 400

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Thin wrapper around the Groq chat completions API.

    Kept deliberately small: nodes depend on this interface (`complete_text`
    / `complete_structured`), so tests can swap in a fake implementation
    without ever hitting the network.
    """

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL) -> None:
        self._api_key = api_key or os.environ.get("GROQ_API_KEY")
        self._model = model
        self._client: Groq | None = None

    @property
    def client(self) -> Groq:
        if self._client is None:
            self._client = Groq(api_key=self._api_key)
        return self._client

    def complete_text(self, system: str, user: str) -> str:
        """Plain chat completion, returns the assistant message content."""
        tracer = get_tracer()
        with tracer.start_as_current_span("llm.complete_text") as span:
            span.set_attribute("llm.model", self._model)
            span.set_attribute("llm.prompt.system", system[:2000])
            span.set_attribute("llm.prompt.user", user[:2000])
            start = time.perf_counter()
            response = self.client.chat.completions.create(
                model=self._model,
                temperature=0.2,
                max_tokens=MAX_OUTPUT_TOKENS,
                reasoning_effort="low",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            span.set_attribute("llm.latency_ms", (time.perf_counter() - start) * 1000)
            content = response.choices[0].message.content or ""
            span.set_attribute("llm.response", content[:2000])
            return content

    def complete_structured(self, system: str, user: str, schema: type[T]) -> T:
        """Chat completion constrained to JSON, validated against `schema`."""
        tracer = get_tracer()
        with tracer.start_as_current_span("llm.complete_structured") as span:
            span.set_attribute("llm.model", self._model)
            span.set_attribute("llm.schema", schema.__name__)
            span.set_attribute("llm.prompt.system", system[:2000])
            span.set_attribute("llm.prompt.user", user[:2000])
            start = time.perf_counter()
            response = self.client.chat.completions.create(
                model=self._model,
                temperature=0,
                max_tokens=MAX_OUTPUT_TOKENS,
                reasoning_effort="low",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": f"{user}\n\nRespond with a single JSON object matching this "
                        f"schema: {schema.model_json_schema()}",
                    },
                ],
            )
            span.set_attribute("llm.latency_ms", (time.perf_counter() - start) * 1000)
            content = response.choices[0].message.content or "{}"
            span.set_attribute("llm.response", content[:2000])
            return schema.model_validate(json.loads(content))
