"""Pydantic response schemas for the spending analysis API.

Defines the data models returned by AnalysisService and serialised as
JSON by the dashboard endpoint: per-day, per-category, per-shop spend,
subscription entries, and the top-level DashboardResponse.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DailySpend(BaseModel):
    """Aggregated spending for a single calendar day.

    Attributes:
        date: ISO 8601 date string (YYYY-MM-DD) or "unknown" for undated items.
        amount: Total amount spent on this date. Must be non-negative.
    """

    model_config = ConfigDict(extra="forbid")
    date: str
    amount: Decimal = Field(ge=Decimal("0.00"))


class SubscriptionSpend(BaseModel):
    """Recurring subscription entry used in spending analysis.

    Attributes:
        name: Subscription service name (e.g. "Netflix", "Spotify").
        amount: Monthly charge amount. Must be non-negative.
        category: Spending category the subscription belongs to.
    """

    model_config = ConfigDict(extra="forbid")
    name: str
    amount: Decimal = Field(ge=Decimal("0.00"))
    category: str


class CategorySpend(BaseModel):
    """Spending grouped by category, with optional budget tracking.

    Attributes:
        category: Category label as extracted from receipt items
            (e.g. "food", "transport", "other").
        amount: Total amount spent in this category. Must be non-negative.
        percentage: Share of total spending, clamped to 0.0-100.0.
        budget_limit: Optional user-defined spending limit for this category.
        budget_utilized_percentage: Percentage of budget consumed
            (amount / budget_limit * 100). None when no budget is set.
    """

    model_config = ConfigDict(extra="forbid")
    category: str
    amount: Decimal = Field(ge=Decimal("0.00"))
    percentage: float = Field(ge=0.0, le=100.0)

    budget_limit: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    budget_utilized_percentage: float | None = Field(default=None, ge=0.0)


class ShopSpend(BaseModel):
    """Spending grouped by merchant, sorted by amount descending.

    Attributes:
        shop_name: Merchant name from receipt, or "Nieznany sklep" when absent.
        amount: Total amount spent at this merchant. Must be non-negative.
    """

    model_config = ConfigDict(extra="forbid")
    shop_name: str
    amount: Decimal = Field(ge=Decimal("0.00"))


class DashboardResponse(BaseModel):
    """Full analytical dashboard for any configurable time period.

    Attributes:
        date_range_label: Human-readable description of the period,
            e.g. "January 2025" or "Last 7 days".
        period_type: Granularity identifier for the period.
        total_spent: Sum of all receipts and subscriptions in the period.
        receipt_count: Number of receipts in the current period.
        daily_average: Average daily spending (total_spent / days_in_period).
        monthly_average: Projected 30-day spend. None for periods shorter
            than 30 days.
        total_spent_trend: Percentage change vs. previous period. None when
            no previous-period data is available.
        receipt_count_trend: Percentage change in receipt count vs. previous
            period. None when no previous-period data is available.
        by_category: Per-category breakdown, sorted by amount descending.
        by_shop: Per-merchant breakdown, sorted by amount descending.
        daily_breakdown: Day-by-day spend series, sorted by date ascending.
    """

    model_config = ConfigDict(extra="forbid")

    date_range_label: str
    period_type: Literal["daily", "weekly", "monthly", "quarterly", "yearly", "all_time"]

    total_spent: Decimal = Field(ge=Decimal("0.00"))
    receipt_count: int = Field(ge=0)
    daily_average: Decimal = Field(ge=Decimal("0.00"))
    monthly_average: Decimal | None = Field(default=None, ge=Decimal("0.00"))

    total_spent_trend: float | None = None
    receipt_count_trend: float | None = None

    by_category: list[CategorySpend]
    by_shop: list[ShopSpend]
    daily_breakdown: list[DailySpend]
