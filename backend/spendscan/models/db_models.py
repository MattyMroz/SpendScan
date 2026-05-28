"""SQLModel database table models."""

# pyright: reportIncompatibleVariableOverride=false
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar, Final

from sqlalchemy import JSON, Column, DateTime, Numeric, Text, func
from sqlmodel import Field, SQLModel

MONEY_PRECISION: Final[int] = 10
MONEY_SCALE: Final[int] = 2


def money_column(nullable: bool = True) -> Column[Decimal]:
    """Return a shared SQL column definition for monetary values."""
    return Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=nullable)


def timestamp_column() -> Column[datetime]:
    """Return a server-managed timestamp column."""
    return Column(DateTime(timezone=False), nullable=False, server_default=func.now())


class User(SQLModel, table=True):
    """User database table."""

    __tablename__: ClassVar[str] = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(sa_column=Column(Text, nullable=False, unique=True))
    email: str = Field(sa_column=Column(Text, nullable=False, unique=True))
    password_hash: str
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class Category(SQLModel, table=True):
    """Category database table."""

    __tablename__: ClassVar[str] = "categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(Text, nullable=False, unique=True))


class Folder(SQLModel, table=True):
    """Folder database table."""

    __tablename__: ClassVar[str] = "folders"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    name: str
    description: str | None = None
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class Receipt(SQLModel, table=True):
    """Analyzed receipt database table."""

    __tablename__: ClassVar[str] = "receipts"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    status: str = "completed"
    merchant_name: str | None = None
    receipt_date: date | None = None
    currency: str = "PLN"
    subtotal_amount: Decimal | None = Field(default=None, sa_column=money_column())
    tax_amount: Decimal | None = Field(default=None, sa_column=money_column())
    total_amount: Decimal = Field(default=Decimal("0.00"), sa_column=money_column(nullable=False))
    total_discount_amount: Decimal | None = Field(default=None, sa_column=money_column())
    payment_method: str | None = None
    raw_ocr_text: str = ""
    warnings: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    error: str | None = None
    importance: int = Field(default=0, nullable=False)
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class ReceiptImage(SQLModel, table=True):
    """Single uploaded image/page belonging to a receipt."""

    __tablename__: ClassVar[str] = "receipt_images"

    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipts.id")
    page_number: int
    original_filename: str
    stored_path: str
    content_type: str | None = None
    ocr_text: str = ""
    ocr_engine: str = ""
    ocr_processing_time_ms: float = 0.0
    image_width: int | None = None
    image_height: int | None = None
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class ReceiptItem(SQLModel, table=True):
    """Single item extracted from a saved receipt."""

    __tablename__: ClassVar[str] = "receipt_items"

    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipts.id")
    product_name: str
    quantity: Decimal | None = Field(default=None, sa_column=money_column())
    unit_price: Decimal | None = Field(default=None, sa_column=money_column())
    total_price: Decimal = Field(sa_column=money_column(nullable=False))
    discount_amount: Decimal | None = Field(default=None, sa_column=money_column())
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
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


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
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class FolderReceipt(SQLModel, table=True):
    """Folder receipt relation table."""

    __tablename__: ClassVar[str] = "folder_receipts"

    id: int | None = Field(default=None, primary_key=True)
    folder_id: int = Field(foreign_key="folders.id")
    receipt_id: int = Field(foreign_key="receipts.id")
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class BudgetReceipt(SQLModel, table=True):
    """Budget receipt relation table."""

    __tablename__: ClassVar[str] = "budget_receipts"

    id: int | None = Field(default=None, primary_key=True)
    budget_id: int = Field(foreign_key="budgets.id")
    receipt_id: int = Field(foreign_key="receipts.id")
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())
