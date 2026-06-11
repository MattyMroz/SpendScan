from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from spendscan.api.app import DATABASE_UNAVAILABLE_MESSAGE
from spendscan.api.dependencies import get_receipt_pipeline
from spendscan.db.database import get_session
from spendscan.llm import ReceiptAnalysisResult, ReceiptItem, ReceiptPipelineResult
from spendscan.ocr import OcrLine, OcrResult
from spendscan.pipeline import MultiImageReceiptPipelineResult, ReceiptImagePipelineResult


class FakePersistentPipeline:
    def __init__(self) -> None:
        self.calls = 0

    async def analyze_receipt_groups(
        self,
        image_path_groups: Sequence[Sequence[Path]],
    ) -> tuple[MultiImageReceiptPipelineResult, ...]:
        return tuple([await self.analyze_images(tuple(image_paths)) for image_paths in image_path_groups])

    async def analyze_images(self, image_paths: Sequence[Path]) -> MultiImageReceiptPipelineResult:
        self.calls += 1
        amount = Decimal(self.calls * 10)
        ocr_results = tuple(
            ReceiptImagePipelineResult(
                image_path=image_path,
                page_number=index,
                ocr=OcrResult(
                    text=f"OCR page {index}",
                    lines=[OcrLine(text=f"OCR page {index}")],
                    engine="fake-ocr",
                    processing_time_ms=1.0,
                    image_shape=(100 + index, 200 + index),
                ),
            )
            for index, image_path in enumerate(image_paths, start=1)
        )
        ocr_text = "\n".join(result.ocr.text for result in ocr_results)
        return MultiImageReceiptPipelineResult(
            receipt=ReceiptPipelineResult(
                ocr_text=ocr_text,
                ocr_engine="fake-ocr",
                ocr_processing_time_ms=float(len(ocr_results)),
                analysis=ReceiptAnalysisResult(
                    merchant_name=f"Shop {self.calls}",
                    receipt_date=date(2026, 5, 21),
                    total_amount=amount,
                    items=[
                        ReceiptItem(
                            name=f"Item {self.calls}",
                            quantity=Decimal("1"),
                            unit_price=amount,
                            total_price=amount,
                            category="food",
                        )
                    ],
                    raw_ocr_text=ocr_text,
                ),
            ),
            images=ocr_results,
        )


class BrokenSession:
    def exec(self, *_args: object, **_kwargs: object) -> object:
        raise OperationalError("SELECT 1", {}, Exception("connection timeout expired"))

    def get(self, *_args: object, **_kwargs: object) -> object:
        raise OperationalError("SELECT 1", {}, Exception("connection timeout expired"))


def _app(api_client: TestClient) -> FastAPI:
    return cast(FastAPI, api_client.app)


def test_create_receipt_persists_two_images(api_client: TestClient) -> None:
    fake_pipeline = FakePersistentPipeline()
    _app(api_client).dependency_overrides[get_receipt_pipeline] = lambda: fake_pipeline

    response = api_client.post(
        "/api/v1/receipts",
        files=[
            ("files", ("receipt_001_1.png", b"first", "image/png")),
            ("files", ("receipt_001_2.png", b"second", "image/png")),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["merchant_name"] == "Shop 1"
    assert len(payload["images"]) == 2
    assert payload["images"][0]["page_number"] == 1
    assert payload["images"][1]["original_filename"] == "receipt_001_2.png"
    assert payload["items"][0]["category"] == "food"

    list_response = api_client.get("/api/v1/receipts")
    assert list_response.status_code == 200
    assert list_response.json()[0]["image_count"] == 2


def test_analyze_pages_runs_multi_image_pipeline_without_persisting(api_client: TestClient) -> None:
    fake_pipeline = FakePersistentPipeline()
    _app(api_client).dependency_overrides[get_receipt_pipeline] = lambda: fake_pipeline

    response = api_client.post(
        "/api/v1/receipts/analyze/pages",
        files=[
            ("files", ("receipt_001_1.png", b"first", "image/png")),
            ("files", ("receipt_001_2.png", b"second", "image/png")),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis"]["merchant_name"] == "Shop 1"
    assert payload["ocr_processing_time_ms"] == 2.0
    assert api_client.get("/api/v1/receipts").json() == []


def test_batch_upload_persists_each_file_as_separate_receipt(api_client: TestClient) -> None:
    fake_pipeline = FakePersistentPipeline()
    _app(api_client).dependency_overrides[get_receipt_pipeline] = lambda: fake_pipeline

    response = api_client.post(
        "/api/v1/receipts/batch",
        files=[
            ("files", ("receipt_001.png", b"first", "image/png")),
            ("files", ("receipt_002.png", b"second", "image/png")),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert [receipt["merchant_name"] for receipt in payload["receipts"]] == ["Shop 1", "Shop 2"]

    dashboard_response = api_client.get("/api/v1/analytics/dashboard?period_type=monthly&reference_date=2026-05-21")
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert Decimal(str(dashboard["total_spent"])) == Decimal("30.00")
    assert dashboard["receipt_count"] == 2
    assert dashboard["by_category"][0]["category"] == "food"


def test_batch_upload_groups_numbered_page_pairs(api_client: TestClient) -> None:
    fake_pipeline = FakePersistentPipeline()
    _app(api_client).dependency_overrides[get_receipt_pipeline] = lambda: fake_pipeline

    response = api_client.post(
        "/api/v1/receipts/batch",
        files=[
            ("files", ("receipt_001_1.png", b"first page", "image/png")),
            ("files", ("receipt_001_2.png", b"second page", "image/png")),
            ("files", ("receipt_002_1.png", b"third page", "image/png")),
            ("files", ("receipt_002_2.png", b"fourth page", "image/png")),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert [receipt["merchant_name"] for receipt in payload["receipts"]] == ["Shop 1", "Shop 2"]
    assert [len(receipt["images"]) for receipt in payload["receipts"]] == [2, 2]
    assert payload["receipts"][0]["images"][0]["original_filename"] == "receipt_001_1.png"
    assert payload["receipts"][1]["images"][1]["original_filename"] == "receipt_002_2.png"


def test_detail_and_delete_receipt(api_client: TestClient) -> None:
    fake_pipeline = FakePersistentPipeline()
    _app(api_client).dependency_overrides[get_receipt_pipeline] = lambda: fake_pipeline
    created = api_client.post(
        "/api/v1/receipts",
        files=[("files", ("receipt.png", b"image", "image/png"))],
    ).json()

    detail_response = api_client.get(f"/api/v1/receipts/{created['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == created["id"]

    delete_response = api_client.delete(f"/api/v1/receipts/{created['id']}")
    assert delete_response.status_code == 204
    assert api_client.get(f"/api/v1/receipts/{created['id']}").status_code == 404
    assert api_client.get("/api/v1/receipts").json() == []


def test_list_receipts_returns_503_when_database_is_unavailable(api_client: TestClient) -> None:
    def override_get_session() -> BrokenSession:
        return BrokenSession()

    _app(api_client).dependency_overrides[get_session] = override_get_session

    response = api_client.get("/api/v1/receipts")

    assert response.status_code == 503
    assert response.json()["detail"] == DATABASE_UNAVAILABLE_MESSAGE


def test_health_db_returns_503_when_database_is_unavailable(api_client: TestClient) -> None:
    def override_get_session() -> BrokenSession:
        return BrokenSession()

    _app(api_client).dependency_overrides[get_session] = override_get_session

    response = api_client.get("/health/db")

    assert response.status_code == 503
    assert response.json()["detail"] == DATABASE_UNAVAILABLE_MESSAGE
