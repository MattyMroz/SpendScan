from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DailySpend(BaseModel):
    """Suma wydatków dla konkretnego dnia."""

    model_config = ConfigDict(extra="forbid")
    date: str
    amount: Decimal


class CategorySpend(BaseModel):
    """Wydatki zgrupowane po kategorii."""

    model_config = ConfigDict(extra="forbid")
    category: str
    amount: Decimal
    percentage: float = Field(ge=0.0, le=100.0)


class ShopSpend(BaseModel):
    """Wydatki zgrupowane po sklepie."""

    model_config = ConfigDict(extra="forbid")
    shop_name: str
    amount: Decimal


class DashboardResponse(BaseModel):
    """Pełny dashboard analityczny dla dowolnego okresu."""

    model_config = ConfigDict(extra="forbid")

    date_range_label: str
    period_type: Literal["weekly", "monthly", "quarterly", "yearly"]

    total_spent: Decimal
    receipt_count: int
    daily_average: Decimal

    total_spent_trend: float | None = None
    receipt_count_trend: float | None = None

    by_category: list[CategorySpend]
    by_shop: list[ShopSpend]
    daily_breakdown: list[DailySpend]
