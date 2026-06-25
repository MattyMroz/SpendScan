"""llama.cpp runtime data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Literal

ContentType = Literal["text", "image_url"]
ChatRole = Literal["user", "assistant", "system", "tool"]


class BackendType(Enum):
    """Native llama.cpp compute backend.

    Controls which prebuilt binary variant is downloaded and which
    hardware acceleration flags are passed to llama-server.
    """

    CUDA = "cuda"
    VULKAN = "vulkan"
    CPU = "cpu"


BACKEND_PRIORITY: Final[tuple[BackendType, ...]] = (
    BackendType.CUDA,
    BackendType.VULKAN,
    BackendType.CPU,
)
"""Preferred backend order for prebuilt llama.cpp binaries."""


@dataclass(frozen=True, slots=True)
class PlatformInfo:
    """Detected platform and preferred llama.cpp compute backend.

    Attributes:
        os: Platform identifier (``sys.platform``), e.g. ``"win32"``.
        arch: Normalized CPU architecture, e.g. ``"x86_64"`` or ``"arm64"``.
        backend: Selected compute backend for llama.cpp.
        cuda_version: NVIDIA driver version string, or ``None`` when CUDA is
            not available.
    """

    os: str
    arch: str
    backend: BackendType
    cuda_version: str | None = None


@dataclass(frozen=True, slots=True)
class ContentPart:
    """Single content part in an OpenAI-compatible multimodal message.

    Attributes:
        type: Part type — ``"text"`` for plain text or ``"image_url"`` for an
            image encoded as a data URI.
        text: Text content; present when ``type`` is ``"text"``.
        image_url: Mapping with a ``"url"`` key containing the data URI;
            present when ``type`` is ``"image_url"``.
    """

    type: ContentType
    text: str | None = None
    image_url: dict[str, str] | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize content part to OpenAI-compatible JSON."""
        payload: dict[str, object] = {"type": self.type}
        if self.text is not None:
            payload["text"] = self.text
        if self.image_url is not None:
            payload["image_url"] = self.image_url
        return payload


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Single message in an OpenAI-compatible chat conversation.

    Attributes:
        role: Conversation role, e.g. ``"user"`` or ``"assistant"``.
        content: Message body — either a plain text string or a list of
            multimodal content parts.
    """

    role: ChatRole
    content: str | list[ContentPart]

    def to_dict(self) -> dict[str, object]:
        """Serialize message to OpenAI-compatible JSON."""
        if isinstance(self.content, str):
            return {"role": self.role, "content": self.content}
        return {"role": self.role, "content": [part.to_dict() for part in self.content]}


@dataclass(frozen=True, slots=True)
class ChatCompletion:
    """Parsed response from a llama-server chat completion request.

    Attributes:
        content: Generated text from the model.
        finish_reason: Stop reason reported by the server (e.g. ``"stop"``
            or ``"length"``).
        usage: Token usage counters keyed by ``"prompt_tokens"``,
            ``"completion_tokens"``, and ``"total_tokens"``.
    """

    content: str
    finish_reason: str = ""
    usage: dict[str, int] = field(default_factory=dict)
