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
    """Typed HTTP client for a running llama-server instance.

    Provides health-check and chat-completion methods over the
    OpenAI-compatible REST API exposed by llama-server.

    Attributes:
        base_url: Base URL of the llama-server instance (no trailing slash).
    """

    __slots__ = ("_client", "base_url")

    def __init__(self, base_url: str, *, timeout: float = 120.0) -> None:
        """Initialize the client pointed at a llama-server base URL.

        Args:
            base_url: Base URL of the server, e.g. ``"http://127.0.0.1:8080"``.
            timeout: Read/write timeout in seconds for inference requests.
                The connection timeout is fixed at 10 seconds.
        """
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
        repeat_penalty: float | None = None,
        repeat_last_n: int | None = None,
    ) -> ChatCompletion:
        """Send a chat completion request and return the parsed response.

        Args:
            messages: Ordered list of messages forming the conversation.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature; 0.0 yields deterministic output.
            repeat_penalty: Penalty factor for repeated tokens.  Omitted from
                the request payload when ``None``.
            repeat_last_n: Lookback window for repeat penalty; ``-1`` covers
                the full context.  Omitted from the payload when ``None``.

        Returns:
            Parsed chat completion with generated content and usage stats.

        Raises:
            LlamaRuntimeError: If the HTTP request fails or the server returns
                a non-2xx status code.
        """
        payload: dict[str, object] = {
            "messages": [message.to_dict() for message in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if repeat_penalty is not None:
            payload["repeat_penalty"] = repeat_penalty
        if repeat_last_n is not None:
            payload["repeat_last_n"] = repeat_last_n
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
