"""HTTP client for llama-server OpenAI-compatible API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import httpx

from .errors import LlamaRuntimeError
from .types import ChatCompletion

if TYPE_CHECKING:
    from .types import ChatMessage

_HEALTH_ENDPOINT: Final[str] = "/health"
_CHAT_ENDPOINT: Final[str] = "/v1/chat/completions"


def _parse_completion(data: dict[str, object]) -> ChatCompletion:
    """Parse raw llama-server JSON into a chat completion."""
    choices = data.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ChatCompletion(content="")

    first = choices[0]
    if not isinstance(first, dict):
        return ChatCompletion(content="")

    message = first.get("message", {})
    if not isinstance(message, dict):
        return ChatCompletion(content="")

    usage_raw = data.get("usage", {})
    usage = usage_raw if isinstance(usage_raw, dict) else {}
    return ChatCompletion(
        content=str(message.get("content", "")),
        finish_reason=str(first.get("finish_reason", "")),
        usage={key: int(value) for key, value in usage.items() if isinstance(value, int | float)},
    )


class LlamaClient:
    """Typed wrapper around a running llama-server instance."""

    __slots__ = ("_client", "base_url")

    def __init__(self, base_url: str, *, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
        )

    def health(self, *, timeout: float = 5.0) -> bool:
        """Return whether llama-server reports healthy status."""
        try:
            response = self._client.get(_HEALTH_ENDPOINT, timeout=timeout)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError):
            return False
        if not isinstance(data, dict):
            return False
        return data.get("status") == "ok"

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> ChatCompletion:
        """Send a chat completion request to llama-server."""
        payload: dict[str, object] = {
            "messages": [message.to_dict() for message in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            response = self._client.post(_CHAT_ENDPOINT, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            msg = f"Chat completion failed (HTTP {exc.response.status_code}): {exc.response.text}"
            raise LlamaRuntimeError(msg) from exc
        except (httpx.HTTPError, ValueError) as exc:
            msg = f"Chat completion request failed: {exc}"
            raise LlamaRuntimeError(msg) from exc

        if not isinstance(data, dict):
            msg = "Chat completion response is not a JSON object"
            raise LlamaRuntimeError(msg)
        return _parse_completion(data)

    def close(self) -> None:
        """Close underlying HTTP connections."""
        self._client.close()

    def __enter__(self) -> LlamaClient:
        """Return this client as a context manager value."""
        return self

    def __exit__(self, *_args: object) -> None:
        """Close the client on context manager exit."""
        self.close()
