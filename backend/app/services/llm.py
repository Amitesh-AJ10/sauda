import json
import os
from typing import TypeVar

from groq import Groq
from pydantic import BaseModel

DEFAULT_MODEL = "qwen/qwen3.8-27b"

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
        response = self.client.chat.completions.create(
            model=self._model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""

    def complete_structured(self, system: str, user: str, schema: type[T]) -> T:
        """Chat completion constrained to JSON, validated against `schema`."""
        response = self.client.chat.completions.create(
            model=self._model,
            temperature=0,
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
        content = response.choices[0].message.content or "{}"
        return schema.model_validate(json.loads(content))
