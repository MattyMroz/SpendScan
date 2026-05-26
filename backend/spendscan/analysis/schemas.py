from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DailySpend(BaseModel):
    """Suma wydatków dla konkretnego dnia."""

    model_config = ConfigDict(extra="forbid")
    date: str
    amount: Decimal = Field(ge=Decimal("0.00"))


class SubscriptionSpend(BaseModel):
    """Subskrypcja do analizy wydatków"""

    model_config = ConfigDict(extra="forbid")
    name: str
    amount: Decimal = Field(ge=Decimal("0.00"))
    category: str


class CategorySpend(BaseModel):
    """Wydatki zgrupowane po kategorii."""

    model_config = ConfigDict(extra="forbid")
    category: str
    amount: Decimal = Field(ge=Decimal("0.00"))
    percentage: float = Field(ge=0.0, le=100.0)

    budget_limit: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    budget_utilized_percentage: float | None = Field(default=None, ge=0.0)


class ShopSpend(BaseModel):
    """Wydatki zgrupowane po sklepie."""

    model_config = ConfigDict(extra="forbid")
    shop_name: str
    amount: Decimal = Field(ge=Decimal("0.00"))


class DashboardResponse(BaseModel):
    """Pełny dashboard analityczny dla dowolnego okresu."""

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
