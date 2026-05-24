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


def test_generate_dashboard_calculates_monthly_average_and_budgets() -> None:
    current_receipts = [
        ReceiptAnalysisResult(
            merchant_name="Biedronka",
            receipt_date="2026-04-10",
            total_amount=Decimal("120.00"),
            currency="PLN",
            items=[ReceiptItem(name="Zakupy", total_price=Decimal("120.00"), category="food")],
        )
    ]

    mock_budgets = {"food": Decimal("300.00")}
    service = AnalysisService()

    result = service.generate_dashboard(
        current_receipts=current_receipts,
        previous_receipts=[],
        date_range_label="Q2 2026",
        period_type="quarterly",
        days_in_period=90,
        category_budgets=mock_budgets,
    )

    assert result.daily_average == Decimal("1.33")

    assert result.monthly_average == Decimal("40.00")

    food_stats = next(c for c in result.by_category if c.category == "food")
    assert food_stats.budget_limit == Decimal("300.00")
    assert food_stats.budget_utilized_percentage == 40.0


def test_generate_dashboard_handles_all_time_period() -> None:
    current_receipts = [ReceiptAnalysisResult(total_amount=Decimal("500.00"), currency="PLN", items=[])]
    service = AnalysisService()

    result = service.generate_dashboard(
        current_receipts=current_receipts,
        previous_receipts=[],
        date_range_label="Od początku",
        period_type="all_time",
        days_in_period=365,
    )

    assert result.period_type == "all_time"
    assert result.total_spent == Decimal("500.00")
    assert result.total_spent_trend is None


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
