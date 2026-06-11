"""Receipt OCR -> LLM analysis pipeline."""

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
    """Pipeline result for one receipt image page."""

    image_path: Path
    page_number: int
    ocr: OcrResult


@dataclass(frozen=True, slots=True)
class MultiImageReceiptPipelineResult:
    """Pipeline result for a receipt that may have multiple image pages."""

    receipt: ReceiptPipelineResult
    images: tuple[ReceiptImagePipelineResult, ...]


class ReceiptPipeline:
    """Minimal receipt analysis pipeline."""

    __slots__ = ("_llm", "_ocr")

    def __init__(self, *, ocr: ReceiptOcrService | None = None, llm: ReceiptLlmClient | None = None) -> None:
        self._ocr = ocr or OcrService()
        self._llm = llm or GeminiReceiptClient()

    async def recognize_image(self, image: ImageInput) -> OcrResult:
        """Run OCR only."""
        return await self._ocr.recognize(image)

    async def analyze_image(self, image_path: Path) -> ReceiptPipelineResult:
        """Run OCR and Gemini parsing for a receipt image."""
        return (await self.analyze_images((image_path,))).receipt

    async def analyze_images(self, image_paths: Sequence[Path]) -> MultiImageReceiptPipelineResult:
        """Run OCR and Gemini parsing for one receipt made of one or more image pages."""
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
        """Run OCR and Gemini parsing for multiple receipts, each with one or more image pages."""
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
