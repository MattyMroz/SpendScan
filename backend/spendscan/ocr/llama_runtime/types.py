"""llama.cpp runtime data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Literal

ContentType = Literal["text", "image_url"]
ChatRole = Literal["user", "assistant", "system", "tool"]


class BackendType(Enum):
    """Native llama.cpp compute backend."""

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
    """Detected platform and preferred llama.cpp backend."""

    os: str
    arch: str
    backend: BackendType
    cuda_version: str | None = None


@dataclass(frozen=True, slots=True)
class ContentPart:
    """Single OpenAI-compatible multimodal content part."""

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
    """Single OpenAI-compatible chat message."""

    role: ChatRole
    content: str | list[ContentPart]

    def to_dict(self) -> dict[str, object]:
        """Serialize message to OpenAI-compatible JSON."""
        if isinstance(self.content, str):
            return {"role": self.role, "content": self.content}
        return {"role": self.role, "content": [part.to_dict() for part in self.content]}


@dataclass(frozen=True, slots=True)
class ChatCompletion:
    """Parsed response from llama-server chat completions."""

    content: str
    finish_reason: str = ""
    usage: dict[str, int] = field(default_factory=dict)
