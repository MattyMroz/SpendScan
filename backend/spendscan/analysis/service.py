"""Business logic for spending analysis."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Literal

from spendscan.analysis.schemas import (
    CategorySpend,
    DailySpend,
    DashboardResponse,
    ShopSpend,
)
from spendscan.llm.schemas import ReceiptAnalysisResult


class AnalysisService:
    """Service for calculating spending statistics and trends."""

    def generate_dashboard(
        self,
        current_receipts: list[ReceiptAnalysisResult],
        previous_receipts: list[ReceiptAnalysisResult],
        date_range_label: str,
        period_type: Literal["weekly", "monthly", "quarterly", "yearly"],
        days_in_period: int,
    ) -> DashboardResponse:
        """
        Calculates dashboard statistics from a list of receipts for any time period.
        """
        total_spent = sum((r.total_amount for r in current_receipts), Decimal("0.00"))
        receipt_count = len(current_receipts)

        if total_spent == Decimal("0.00") or days_in_period <= 0:
            return DashboardResponse(
                date_range_label=date_range_label,
                period_type=period_type,
                total_spent=total_spent,
                receipt_count=receipt_count,
                daily_average=Decimal("0.00"),
                total_spent_trend=None,
                receipt_count_trend=None,
                by_category=[],
                by_shop=[],
                daily_breakdown=[],
            )

        shop_totals: defaultdict[str, Decimal] = defaultdict(Decimal)
        category_totals: defaultdict[str, Decimal] = defaultdict(Decimal)
        daily_totals: defaultdict[str, Decimal] = defaultdict(Decimal)

        for receipt in current_receipts:
            shop_name = receipt.merchant_name or "Nieznany sklep"
            shop_totals[shop_name] += receipt.total_amount

            date_key = str(receipt.receipt_date) if receipt.receipt_date else "unknown"
            daily_totals[date_key] += receipt.total_amount

            for item in receipt.items:
                cat_name = item.category or "other"
                category_totals[cat_name] += item.total_price

        prev_total = sum((r.total_amount for r in previous_receipts), Decimal("0.00"))
        prev_count = len(previous_receipts)

        spent_trend: float | None = None
        if prev_total > Decimal("0.00"):
            spent_trend = float((total_spent - prev_total) / prev_total * Decimal("100"))

        count_trend: float | None = None
        if prev_count > 0:
            count_trend = float((receipt_count - prev_count) / prev_count * 100)

        # UNIWERSALNA ŚREDNIA DZIENNA
        daily_average = total_spent / Decimal(str(days_in_period))

        shops = [ShopSpend(shop_name=name, amount=amount) for name, amount in shop_totals.items()]
        shops.sort(key=lambda x: x.amount, reverse=True)

        categories: list[CategorySpend] = []
        for cat_name, cat_amount in category_totals.items():
            percentage = float(cat_amount / total_spent * Decimal("100"))
            categories.append(
                CategorySpend(
                    category=cat_name,
                    amount=cat_amount,
                    percentage=round(percentage, 2),
                )
            )
        categories.sort(key=lambda x: x.amount, reverse=True)

        daily_breakdown = [
            DailySpend(date=date_val, amount=amount) for date_val, amount in sorted(daily_totals.items())
        ]

        return DashboardResponse(
            date_range_label=date_range_label,
            period_type=period_type,
            total_spent=total_spent,
            receipt_count=receipt_count,
            daily_average=round(daily_average, 2),
            total_spent_trend=round(spent_trend, 1) if spent_trend is not None else None,
            receipt_count_trend=round(count_trend, 1) if count_trend is not None else None,
            by_category=categories,
            by_shop=shops,
            daily_breakdown=daily_breakdown,
        )
