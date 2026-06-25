"""Receipt OCR -> LLM analysis pipeline.

Provides the ReceiptPipeline class that orchestrates the full flow:
image input → OCR text extraction → Gemini LLM structured parsing → result.
Supports single-image, multi-image (multi-page), and batch (multi-receipt) modes.

Typical usage:

    pipeline = ReceiptPipeline()
    result = await pipeline.analyze_image(Path("receipt.jpg"))
    print(result.analysis.total_amount)
"""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from spendscan.errors import ExternalServiceError
from spendscan.llm import GeminiReceiptClient, ReceiptAnalysisResult, ReceiptPipelineResult
from spendscan.ocr import ImageInput, OcrResult, OcrService


class ReceiptOcrService(Protocol):
    """OCR service required by the receipt pipeline."""

    async def recognize(self, image: ImageInput) -> OcrResult:
        """Recognize text in an image."""
        ...


class ReceiptLlmClient(Protocol):
    """LLM client required by the receipt pipeline."""

    async def analyze_receipt(
        self,
        *,
        ocr_text: str,
        image_path: Path | None = None,
        image_paths: Sequence[Path] | None = None,
    ) -> ReceiptAnalysisResult:
        """Analyze OCR text into receipt JSON."""
        ...


@dataclass(frozen=True, slots=True)
class ReceiptImagePipelineResult:
    """Pipeline result for one receipt image page.

    Attributes:
        image_path: Path to the source image file.
        page_number: 1-based page index within the multi-page receipt.
        ocr: Raw OCR result including text, engine name, and timing.
    """

    image_path: Path
    page_number: int
    ocr: OcrResult


@dataclass(frozen=True, slots=True)
class MultiImageReceiptPipelineResult:
    """Pipeline result for a receipt that may have multiple image pages.

    Attributes:
        receipt: Aggregated pipeline result containing combined OCR text
            and the LLM-parsed structured analysis.
        images: Per-page OCR results in page order.
    """

    receipt: ReceiptPipelineResult
    images: tuple[ReceiptImagePipelineResult, ...]


class ReceiptPipeline:
    """Orchestrate the OCR → LLM receipt analysis flow.

    Coordinates an OCR service and an LLM client to convert receipt images
    into structured financial data. Supports single images, multi-page
    receipts (several images belonging to one receipt), and batches of
    independent receipts.

    Example:
        >>> pipeline = ReceiptPipeline()
        >>> result = await pipeline.analyze_image(Path("receipt.jpg"))
        >>> result.analysis.total_amount
        Decimal('42.99')
    """

    __slots__ = ("_llm", "_ocr")

    def __init__(self, *, ocr: ReceiptOcrService | None = None, llm: ReceiptLlmClient | None = None) -> None:
        """Initialize the pipeline with optional service overrides.

        Args:
            ocr: OCR service to use. Defaults to OcrService().
            llm: LLM client to use. Defaults to GeminiReceiptClient().
        """
        self._ocr = ocr or OcrService()
        self._llm = llm or GeminiReceiptClient()

    async def recognize_image(self, image: ImageInput) -> OcrResult:
        """Run OCR only."""
        return await self._ocr.recognize(image)

    async def analyze_image(self, image_path: Path) -> ReceiptPipelineResult:
        """Run OCR and Gemini parsing for a single-image receipt.

        Convenience wrapper around analyze_images for the common case of
        one image per receipt. Returns only the aggregated receipt result,
        discarding per-page detail.

        Args:
            image_path: Path to the receipt image file.

        Returns:
            Aggregated pipeline result with OCR text and LLM analysis.

        Raises:
            ValueError: If image_path cannot be processed by the OCR service.
            ExternalServiceError: If the OCR step fails completely.
        """
        return (await self.analyze_images((image_path,))).receipt

    async def analyze_images(self, image_paths: Sequence[Path]) -> MultiImageReceiptPipelineResult:
        """Run OCR and Gemini parsing for one receipt made of one or more image pages.

        Runs OCR on each image sequentially, combines the text, then sends
        the combined text (and image paths) to the LLM. If some but not all
        pages fail OCR, a zero-total result with warnings is returned instead
        of calling the LLM.

        Args:
            image_paths: Ordered sequence of image paths representing pages
                of a single receipt (first page first).

        Returns:
            MultiImageReceiptPipelineResult containing the aggregated receipt
            analysis and per-page OCR details.

        Raises:
            ValueError: If image_paths is empty.
            ExternalServiceError: If every OCR page fails.
        """
        if not image_paths:
            msg = "At least one receipt image is required"
            raise ValueError(msg)

        collected_results: list[ReceiptImagePipelineResult] = []
        for index, image_path in enumerate(image_paths, start=1):
            collected_results.append(
                ReceiptImagePipelineResult(
                    image_path=image_path,
                    page_number=index,
                    ocr=await self._ocr.recognize(image_path),
                )
            )
        image_results = tuple(collected_results)
        ocr_text = _combined_ocr_text(image_results)
        ocr_errors = [f"page {result.page_number}: {result.ocr.error}" for result in image_results if result.ocr.error]
        if ocr_errors and len(ocr_errors) == len(image_results):
            msg = "All OCR pages failed: " + "; ".join(ocr_errors)
            raise ExternalServiceError(msg)
        if ocr_errors:
            analysis = ReceiptAnalysisResult(
                total_amount=Decimal("0"),
                raw_ocr_text=ocr_text,
                warnings=ocr_errors,
            )
        else:
            analysis = await self._llm.analyze_receipt(ocr_text=ocr_text, image_paths=tuple(image_paths))

        receipt = ReceiptPipelineResult(
            ocr_text=ocr_text,
            ocr_engine=_combined_ocr_engine(image_results),
            ocr_processing_time_ms=sum(result.ocr.processing_time_ms for result in image_results),
            analysis=analysis,
        )
        return MultiImageReceiptPipelineResult(receipt=receipt, images=image_results)

    async def analyze_receipt_groups(
        self,
        image_path_groups: Sequence[Sequence[Path]],
    ) -> tuple[MultiImageReceiptPipelineResult, ...]:
        """Run OCR and Gemini parsing for multiple receipts, each with one or more image pages.

        Processes each receipt group independently in sequence. Useful when
        a single upload contains several distinct receipts, each of which
        may itself span multiple pages.

        Args:
            image_path_groups: Sequence of receipt groups; each inner
                sequence is an ordered list of image pages for one receipt.

        Returns:
            Tuple of results in the same order as image_path_groups.

        Raises:
            ValueError: If image_path_groups is empty.
            ExternalServiceError: If all OCR pages in any single receipt fail.
        """
        if not image_path_groups:
            msg = "At least one receipt image group is required"
            raise ValueError(msg)

        return tuple([await self.analyze_images(tuple(image_paths)) for image_paths in image_path_groups])

    async def cleanup(self) -> None:
        """Release pipeline resources when the OCR service supports cleanup."""
        cleanup = getattr(self._ocr, "cleanup", None)
        if not callable(cleanup):
            return
        result = cleanup()
        if inspect.isawaitable(result):
            await result


def _combined_ocr_text(image_results: tuple[ReceiptImagePipelineResult, ...]) -> str:
    if len(image_results) == 1:
        return image_results[0].ocr.text
    pages = [
        f"--- PAGE {result.page_number}: {result.image_path.name} ---\n{result.ocr.text.strip()}"
        for result in image_results
    ]
    return "\n\n".join(pages).strip()


def _combined_ocr_engine(image_results: tuple[ReceiptImagePipelineResult, ...]) -> str:
    engines = tuple(dict.fromkeys(result.ocr.engine for result in image_results if result.ocr.engine))
    return ", ".join(engines)
