from __future__ import annotations

from decimal import Decimal

from spendscan.analysis.service import AnalysisService
from spendscan.llm.schemas import ReceiptAnalysisResult, ReceiptItem


def test_generate_dashboard_calculates_correct_totals_and_trends() -> None:
    current_receipts = [
        ReceiptAnalysisResult(
            merchant_name="Biedronka",
            receipt_date="2026-04-05",
            total_amount=Decimal("100.00"),
            currency="PLN",
            items=[ReceiptItem(name="Ser", total_price=Decimal("100.00"), category="food")],
        ),
        ReceiptAnalysisResult(
            merchant_name="Lidl",
            receipt_date="2026-04-06",
            total_amount=Decimal("50.00"),
            currency="PLN",
            items=[ReceiptItem(name="Mydło", total_price=Decimal("50.00"), category="household")],
        ),
    ]

    previous_receipts = [
        ReceiptAnalysisResult(
            merchant_name="Biedronka",
            receipt_date="2026-03-29",
            total_amount=Decimal("100.00"),
            currency="PLN",
            items=[],
        )
    ]

    service = AnalysisService()

    result = service.generate_dashboard(
        current_receipts=current_receipts,
        previous_receipts=previous_receipts,
        date_range_label="01 - 07 kwi 2026",
        period_type="weekly",
        days_in_period=7,
    )

    assert result.total_spent == Decimal("150.00")
    assert result.receipt_count == 2
    assert result.daily_average == Decimal("21.43")

    assert result.period_type == "weekly"
    assert len(result.daily_breakdown) == 2
    assert result.daily_breakdown[0].date == "2026-04-05"
    assert result.daily_breakdown[0].amount == Decimal("100.00")

    assert result.total_spent_trend == 50.0
    assert result.receipt_count_trend == 100.0


def test_generate_dashboard_handles_no_previous_data() -> None:
    current_receipts = [ReceiptAnalysisResult(total_amount=Decimal("50.00"), currency="PLN", items=[])]
    service = AnalysisService()

    result = service.generate_dashboard(
        current_receipts=current_receipts,
        previous_receipts=[],
        date_range_label="Miesiąc bez historii",
        period_type="monthly",
        days_in_period=30,
    )

    assert result.total_spent == Decimal("50.00")
    assert result.total_spent_trend is None
    assert result.receipt_count_trend is None


def test_generate_dashboard_handles_empty_receipts() -> None:
    service = AnalysisService()

    result = service.generate_dashboard(
        current_receipts=[],
        previous_receipts=[],
        date_range_label="Pusty kwartał",
        period_type="quarterly",
        days_in_period=90,
    )

    assert result.total_spent == Decimal("0.00")
    assert result.daily_average == Decimal("0.00")
    assert result.total_spent_trend is None
    assert len(result.by_shop) == 0
    assert len(result.daily_breakdown) == 0
