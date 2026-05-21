"""SQLModel database table models."""

# pyright: reportIncompatibleVariableOverride=false
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User database table."""

    __tablename__: ClassVar[str] = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str
    email: str
    password_hash: str
    created_at: datetime | None = None


class Category(SQLModel, table=True):
    """Category database table."""

    __tablename__: ClassVar[str] = "categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str


class Folder(SQLModel, table=True):
    """Folder database table."""

    __tablename__: ClassVar[str] = "folders"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    name: str
    description: str | None = None
    created_at: datetime | None = None


class Receipt(SQLModel, table=True):
    """Receipt database table."""

    __tablename__: ClassVar[str] = "receipts"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    image_path: str | None = None
    shop_name: str
    purchase_date: date
    total_amount: int
    description: str | None = None
    importance_level: int | None = None
    created_at: datetime | None = None


class ReceiptItem(SQLModel, table=True):
    """Receipt item database table."""

    __tablename__: ClassVar[str] = "receipt_items"

    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipts.id")
    product_name: str
    price: int
    quantity: Decimal = Field(default=Decimal("1.00"), max_digits=10, decimal_places=2)
    category_id: int | None = Field(default=None, foreign_key="categories.id")


class Subscription(SQLModel, table=True):
    """Subscription database table."""

    __tablename__: ClassVar[str] = "subscriptions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    name: str
    amount: int
    billing_cycle: str
    next_payment_date: date
    category_id: int | None = Field(default=None, foreign_key="categories.id")
    is_active: int = 1
    created_at: datetime | None = None


class Budget(SQLModel, table=True):
    """Budget database table."""

    __tablename__: ClassVar[str] = "budgets"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    name: str
    description: str | None = None
    category_id: int | None = Field(default=None, foreign_key="categories.id")
    amount_limit: int
    period_type: str
    alert_threshold_percent: int = 80
    is_active: int = 1
    created_at: datetime | None = None


class FolderReceipt(SQLModel, table=True):
    """Folder receipt relation table."""

    __tablename__: ClassVar[str] = "folder_receipts"

    id: int | None = Field(default=None, primary_key=True)
    folder_id: int = Field(foreign_key="folders.id")
    receipt_id: int = Field(foreign_key="receipts.id")
    created_at: datetime | None = None


class BudgetReceipt(SQLModel, table=True):
    """Budget receipt relation table."""

    __tablename__: ClassVar[str] = "budget_receipts"

    id: int | None = Field(default=None, primary_key=True)
    budget_id: int = Field(foreign_key="budgets.id")
    receipt_id: int = Field(foreign_key="receipts.id")
    created_at: datetime | None = None
