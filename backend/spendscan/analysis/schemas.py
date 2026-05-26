from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DailySpend(BaseModel):
    """Suma wydatków dla konkretnego dnia."""

    model_config = ConfigDict(extra="forbid")
    date: str
    amount: Decimal


class SubscriptionSpend(BaseModel):
    """Subskrypcja do analizy wydatków"""

    model_config = ConfigDict(extra="forbid")
    name: str
    amount: Decimal
    category: str


class CategorySpend(BaseModel):
    """Wydatki zgrupowane po kategorii."""

    model_config = ConfigDict(extra="forbid")
    category: str
    amount: Decimal
    percentage: float = Field(ge=0.0, le=100.0)

    budget_limit: Decimal | None = None
    budget_utilized_percentage: float | None = None


class ShopSpend(BaseModel):
    """Wydatki zgrupowane po sklepie."""

    model_config = ConfigDict(extra="forbid")
    shop_name: str
    amount: Decimal


class DashboardResponse(BaseModel):
    """Pełny dashboard analityczny dla dowolnego okresu."""

    model_config = ConfigDict(extra="forbid")

    date_range_label: str
    period_type: Literal["daily", "weekly", "monthly", "quarterly", "yearly", "all_time"]

    total_spent: Decimal
    receipt_count: int
    daily_average: Decimal
    monthly_average: Decimal | None = None

    total_spent_trend: float | None = None
    receipt_count_trend: float | None = None

    by_category: list[CategorySpend]
    by_shop: list[ShopSpend]
    daily_breakdown: list[DailySpend]
