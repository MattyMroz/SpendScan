"""SQLModel ORM table definitions for the SpendScan database.

Defines all persistent entities: User, Category, Folder, Receipt,
ReceiptImage, ReceiptItem, Subscription, Budget, FolderReceipt, and
BudgetReceipt. Monetary values are stored as integer cents; quantities
use a fixed-precision Decimal column.
"""

from __future__ import annotations

# pyright: reportIncompatibleVariableOverride=false
from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar, Final

from sqlalchemy import JSON, Column, DateTime, Integer, LargeBinary, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

QUANTITY_PRECISION: Final[int] = 10
QUANTITY_SCALE: Final[int] = 2


def money_column(nullable: bool = True) -> Column[int]:
    """Return a shared SQL column definition for monetary values stored as cents."""
    return Column(Integer, nullable=nullable)


def json_column(nullable: bool = True) -> Column[list[str]]:
    """Return a JSON column compatible with PostgreSQL and SQLite."""
    return Column(JSON().with_variant(JSONB, "postgresql"), nullable=nullable)


def quantity_column(nullable: bool = True) -> Column[Decimal]:
    """Return a shared SQL column definition for item quantities."""
    return Column(Numeric(QUANTITY_PRECISION, QUANTITY_SCALE), nullable=nullable)


def timestamp_column() -> Column[datetime]:
    """Return a server-managed timestamp column."""
    return Column(DateTime(timezone=False), nullable=False, server_default=func.now())


class User(SQLModel, table=True):
    """Registered application user.

    Attributes:
        id: Auto-assigned primary key.
        username: Unique display name.
        email: Unique email address used for login.
        password_hash: Bcrypt hash of the user's password.
        created_at: Server-assigned creation timestamp.
    """

    __tablename__: ClassVar[str] = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(sa_column=Column(Text, nullable=False, unique=True))
    email: str = Field(sa_column=Column(Text, nullable=False, unique=True))
    password_hash: str
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class Category(SQLModel, table=True):
    """Expense category used to classify receipt items and subscriptions.

    Attributes:
        id: Auto-assigned primary key.
        name: Unique, normalised (lowercase) category label.
    """

    __tablename__: ClassVar[str] = "categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(Text, nullable=False, unique=True))


class Folder(SQLModel, table=True):
    """User-defined grouping that can contain multiple receipts.

    Attributes:
        id: Auto-assigned primary key.
        user_id: Owner of this folder (FK → users).
        name: Display name of the folder.
        description: Optional free-text description.
        created_at: Server-assigned creation timestamp.
    """

    __tablename__: ClassVar[str] = "folders"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    name: str
    description: str | None = None
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class Receipt(SQLModel, table=True):
    """Analysed receipt produced by the OCR/LLM pipeline.

    Monetary fields (subtotal_amount, tax_amount, total_amount,
    total_discount_amount) are stored as integer cents.

    Attributes:
        id: Auto-assigned primary key.
        user_id: Owner of this receipt (FK → users).
        status: Processing status, e.g. ``"completed"``.
        merchant_name: Store or vendor name extracted from the receipt.
        receipt_date: Date printed on the receipt.
        currency: ISO 4217 currency code, default ``"PLN"``.
        total_amount: Grand total in cents (always present).
        payment_method: Payment method string from the receipt.
        raw_ocr_text: Concatenated OCR output from all pages.
        warnings: Non-fatal pipeline warnings collected during analysis.
        importance: User-assigned importance level, 0-3.
        created_at: Server-assigned creation timestamp.
    """

    __tablename__: ClassVar[str] = "receipts"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    status: str = "completed"
    merchant_name: str | None = None
    receipt_date: date | None = None
    currency: str = "PLN"
    subtotal_amount: int | None = Field(default=None, sa_column=money_column())
    tax_amount: int | None = Field(default=None, sa_column=money_column())
    total_amount: int = Field(default=0, sa_column=money_column(nullable=False))
    total_discount_amount: int | None = Field(default=None, sa_column=money_column())
    payment_method: str | None = None
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    raw_ocr_text: str = ""
    warnings: list[str] = Field(default_factory=list, sa_column=json_column(nullable=False))
    error: str | None = None
    importance: int = Field(default=0, nullable=False)
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class ReceiptImage(SQLModel, table=True):
    """Single uploaded image page belonging to a receipt.

    Each multi-page receipt upload produces one ReceiptImage per page.
    The raw bytes may be stored either on-disk (stored_path) or inline
    in the database (image_data).

    Attributes:
        id: Auto-assigned primary key.
        receipt_id: Parent receipt (FK → receipts).
        page_number: 1-based page index within the receipt.
        original_filename: Client-provided filename at upload time.
        stored_path: POSIX path to the file if stored on disk; None otherwise.
        image_data: Raw image bytes when stored inline in the DB.
        content_type: MIME type reported by the client.
        ocr_text: OCR output for this specific page.
        ocr_engine: Identifier of the OCR engine used.
        ocr_processing_time_ms: Wall-clock OCR duration in milliseconds.
        image_width: Pixel width of the image, if known.
        image_height: Pixel height of the image, if known.
        created_at: Server-assigned creation timestamp.
    """

    __tablename__: ClassVar[str] = "receipt_images"

    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipts.id")
    page_number: int
    original_filename: str
    stored_path: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    image_data: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    content_type: str | None = None
    ocr_text: str = ""
    ocr_engine: str = ""
    ocr_processing_time_ms: float = 0.0
    image_width: int | None = None
    image_height: int | None = None
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class ReceiptItem(SQLModel, table=True):
    """Single line item extracted from a receipt by the LLM pipeline.

    Monetary values (unit_price, total_price, discount_amount) are stored
    as integer cents.

    Attributes:
        id: Auto-assigned primary key.
        receipt_id: Parent receipt (FK → receipts).
        product_name: Name of the purchased product.
        quantity: Item quantity; supports fractional amounts.
        unit_price: Price per unit in cents.
        total_price: Line total in cents (quantity x unit_price after discounts).
        discount_amount: Per-line discount in cents.
        category_id: Optional category (FK → categories).
    """

    __tablename__: ClassVar[str] = "receipt_items"

    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipts.id")
    product_name: str
    quantity: Decimal | None = Field(default=None, sa_column=quantity_column())
    unit_price: int | None = Field(default=None, sa_column=money_column())
    total_price: int = Field(default=0, sa_column=money_column(nullable=False))
    discount_amount: int | None = Field(default=None, sa_column=money_column())
    category_id: int | None = Field(default=None, foreign_key="categories.id")


class Subscription(SQLModel, table=True):
    """Recurring subscription tracked by the user.

    Attributes:
        id: Auto-assigned primary key.
        user_id: Owner of the subscription (FK → users).
        name: Human-readable subscription name.
        amount: Recurring charge in cents.
        billing_cycle: Billing frequency string, e.g. ``"monthly"``.
        next_payment_date: Date of the upcoming charge.
        category_id: Optional expense category (FK → categories).
        is_active: 1 if active, 0 if cancelled.
        created_at: Server-assigned creation timestamp.
    """

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
    """Spending budget with configurable period and alert threshold.

    Attributes:
        id: Auto-assigned primary key.
        user_id: Owner of the budget (FK → users).
        name: Human-readable budget name.
        description: Optional free-text description.
        category_id: Optional category this budget applies to (FK → categories).
        amount_limit: Maximum allowed spend in cents for the period.
        period_type: Period granularity, e.g. ``"monthly"`` or ``"yearly"``.
        alert_threshold_percent: Spend percentage that triggers an alert (default 80).
        is_active: 1 if active, 0 if archived.
        created_at: Server-assigned creation timestamp.
    """

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
    """Many-to-many link between a folder and a receipt.

    Attributes:
        id: Auto-assigned primary key.
        folder_id: FK → folders.
        receipt_id: FK → receipts.
        created_at: Server-assigned creation timestamp.
    """

    __tablename__: ClassVar[str] = "folder_receipts"

    id: int | None = Field(default=None, primary_key=True)
    folder_id: int = Field(foreign_key="folders.id")
    receipt_id: int = Field(foreign_key="receipts.id")
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())


class BudgetReceipt(SQLModel, table=True):
    """Many-to-many link between a budget and a receipt.

    Attributes:
        id: Auto-assigned primary key.
        budget_id: FK → budgets.
        receipt_id: FK → receipts.
        created_at: Server-assigned creation timestamp.
    """

    __tablename__: ClassVar[str] = "budget_receipts"

    id: int | None = Field(default=None, primary_key=True)
    budget_id: int = Field(foreign_key="budgets.id")
    receipt_id: int = Field(foreign_key="receipts.id")
    created_at: datetime | None = Field(default=None, sa_column=timestamp_column())
