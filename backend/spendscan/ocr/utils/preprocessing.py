"""Image validation, conversion, and resizing for OCR."""

from __future__ import annotations

from pathlib import Path
from typing import Final, assert_never

import numpy as np
from PIL import Image

from spendscan.ocr.types import ImageInput

DEFAULT_MAX_IMAGE_DIMENSION: Final[int] = 2048
"""Default longest-edge pixel limit before resize."""

DEFAULT_MIN_IMAGE_DIMENSION: Final[int] = 64
"""Default minimum accepted image edge size."""


def validate_and_resize_image(
    image: ImageInput,
    *,
    max_dimension: int = DEFAULT_MAX_IMAGE_DIMENSION,
    min_dimension: int = DEFAULT_MIN_IMAGE_DIMENSION,
    convert_rgb: bool = True,
) -> tuple[Image.Image, tuple[int, int], bool]:
    """Validate an image and resize it when the longest edge is too large."""
    pil_image = convert_to_pil(image)
    original_shape = (pil_image.height, pil_image.width)
    _validate_minimum_size(pil_image, min_dimension)

    if convert_rgb:
        pil_image = pil_image.convert("RGB")

    return _resize_if_needed(pil_image, max_dimension, min_dimension, original_shape)


def convert_to_pil(image: ImageInput) -> Image.Image:
    """Convert a supported image input into a loaded PIL image."""
    if isinstance(image, str | Path):
        image_path = Path(image)
        if not image_path.exists():
            msg = f"Image not found: {image_path}"
            raise FileNotFoundError(msg)
        with Image.open(image_path) as opened:
            opened.load()
            return opened.copy()

    if isinstance(image, np.ndarray):
        return _ndarray_to_pil(image)

    if isinstance(image, Image.Image):
        return image

    assert_never(image)


def _ndarray_to_pil(image: np.ndarray) -> Image.Image:
    if image.ndim == 2:
        return Image.fromarray(image, mode="L")
    if image.ndim == 3:
        mode_map = {3: "RGB", 4: "RGBA"}
        mode = mode_map.get(image.shape[2])
        if mode is not None:
            return Image.fromarray(image, mode=mode)
    msg = f"Unsupported numpy array shape: {image.shape}. Expected (H,W), (H,W,3), or (H,W,4)."
    raise ValueError(msg)


def _validate_minimum_size(image: Image.Image, min_dimension: int) -> None:
    if image.width >= min_dimension and image.height >= min_dimension:
        return
    msg = f"Image too small: {image.width}x{image.height}px. Minimum: {min_dimension}x{min_dimension}px."
    raise ValueError(msg)


def _resize_if_needed(
    image: Image.Image,
    max_dimension: int,
    min_dimension: int,
    original_shape: tuple[int, int],
) -> tuple[Image.Image, tuple[int, int], bool]:
    longest_edge = max(image.width, image.height)
    if longest_edge <= max_dimension:
        return image, original_shape, False

    scale = max_dimension / longest_edge
    new_width = max(int(image.width * scale), min_dimension)
    new_height = max(int(image.height * scale), min_dimension)
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized, original_shape, True
