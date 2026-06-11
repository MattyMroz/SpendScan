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
    SubscriptionSpend,
)
from spendscan.llm.schemas import ReceiptAnalysisResult


class AnalysisService:
    """Service for calculating spending statistics and trends."""

    def generate_dashboard(
        self,
        current_receipts: list[ReceiptAnalysisResult],
        previous_receipts: list[ReceiptAnalysisResult],
        date_range_label: str,
        period_type: Literal["daily", "weekly", "monthly", "quarterly", "yearly", "all_time"],
        days_in_period: int,
        category_budgets: dict[str, Decimal] | None = None,
        current_subscriptions: list[SubscriptionSpend] | None = None,
        previous_subscriptions: list[SubscriptionSpend] | None = None,
    ) -> DashboardResponse:
        """
        Calculates dashboard statistics from a list of receipts for any time period.
        """
        curr_subs = current_subscriptions or []
        prev_subs = previous_subscriptions or []

        receipts_total = sum((r.total_amount for r in current_receipts), Decimal("0.00"))
        subs_total = sum((s.amount for s in curr_subs), Decimal("0.00"))
        total_spent = receipts_total + subs_total
        receipt_count = len(current_receipts)

        if total_spent == Decimal("0.00") or days_in_period <= 0:
            return DashboardResponse(
                date_range_label=date_range_label,
                period_type=period_type,
                total_spent=total_spent,
                receipt_count=receipt_count,
                daily_average=Decimal("0.00"),
                monthly_average=None,
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

        for sub in curr_subs:
            category_totals[sub.category] += sub.amount

        prev_receipts_total = sum((r.total_amount for r in previous_receipts), Decimal("0.00"))
        prev_subs_total = sum((s.amount for s in prev_subs), Decimal("0.00"))
        prev_total = prev_receipts_total + prev_subs_total
        prev_count = len(previous_receipts)

        spent_trend: float | None = None
        if prev_total > Decimal("0.00"):
            spent_trend = float((total_spent - prev_total) / prev_total * Decimal("100"))

        count_trend: float | None = None
        if prev_count > 0:
            count_trend = float((receipt_count - prev_count) / prev_count * 100)

        daily_average = total_spent / Decimal(str(days_in_period))
        monthly_average: Decimal | None = None
        if days_in_period >= 30:
            monthly_average = daily_average * Decimal("30")

        shops = [ShopSpend(shop_name=name, amount=amount) for name, amount in shop_totals.items()]
        shops.sort(key=lambda x: x.amount, reverse=True)

        categories: list[CategorySpend] = []
        budgets = category_budgets or {}
        for cat_name, cat_amount in category_totals.items():
            # Decimal->float roundtrip can give 100.0000000001; CategorySpend has le=100.0 constraint.
            percentage = float(cat_amount / total_spent * Decimal("100")) if total_spent > Decimal("0") else 0.0
            percentage = max(0.0, min(100.0, round(percentage, 2)))

            limit = budgets.get(cat_name)
            utilized_pct: float | None = None
            if limit and limit > Decimal("0.00"):
                utilized_pct = round(float((cat_amount / limit) * Decimal("100")), 1)

            categories.append(
                CategorySpend(
                    category=cat_name,
                    amount=cat_amount,
                    percentage=percentage,
                    budget_limit=limit,
                    budget_utilized_percentage=utilized_pct,
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
            monthly_average=round(monthly_average, 2) if monthly_average else None,
            total_spent_trend=round(spent_trend, 1) if spent_trend is not None else None,
            receipt_count_trend=round(count_trend, 1) if count_trend is not None else None,
            by_category=categories,
            by_shop=shops,
            daily_breakdown=daily_breakdown,
        )
