"""Analytics endpoints backed by persisted receipts."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from spendscan.analysis import AnalysisService, DashboardResponse
from spendscan.api.dependencies import SessionDep
from spendscan.auth import CurrentUser
from spendscan.db.repositories import ReceiptRepository

router = APIRouter(prefix="/analytics", tags=["analytics"])
PeriodType = Literal["daily", "weekly", "monthly", "quarterly", "yearly", "all_time"]


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    session: SessionDep,
    current_user: CurrentUser,
    period_type: Annotated[PeriodType, Query(description="Dashboard period type.")] = "monthly",
    reference_date: Annotated[date | None, Query(description="Date inside the requested period.")] = None,
) -> DashboardResponse:
    """Return dashboard statistics calculated from persisted receipts."""
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")
    resolved_reference_date = reference_date or date.today()
    current_start, current_end = _period_bounds(period_type, resolved_reference_date)
    previous_start, previous_end = _previous_period_bounds(period_type, current_start)
    repository = ReceiptRepository(session)
    return AnalysisService().generate_dashboard(
        current_receipts=repository.list_analysis_results(
            start_date=current_start, end_date=current_end, user_id=current_user.id
        ),
        previous_receipts=repository.list_analysis_results(
            start_date=previous_start, end_date=previous_end, user_id=current_user.id
        ),
        date_range_label=f"{current_start.isoformat()} - {current_end.isoformat()}",
        period_type=period_type,
        days_in_period=(current_end - current_start).days + 1,
        category_budgets={},
    )


def _period_bounds(period_type: PeriodType, reference_date: date) -> tuple[date, date]:
    """Return the inclusive start and end dates for the period containing reference_date.

    Args:
        period_type: Granularity of the period.
        reference_date: Any date within the desired period.

    Returns:
        Tuple of (start, end) dates, both inclusive.
    """
    if period_type == "daily":
        return reference_date, reference_date
    if period_type == "all_time":
        return date(2000, 1, 1), reference_date
    if period_type == "weekly":
        start = reference_date - timedelta(days=reference_date.weekday())
        return start, start + timedelta(days=6)
    if period_type == "monthly":
        start = reference_date.replace(day=1)
        return start, _next_month(start) - timedelta(days=1)
    if period_type == "quarterly":
        quarter_start_month = ((reference_date.month - 1) // 3) * 3 + 1
        start = reference_date.replace(month=quarter_start_month, day=1)
        return start, _add_months(start, 3) - timedelta(days=1)
    start = reference_date.replace(month=1, day=1)
    return start, start.replace(year=start.year + 1) - timedelta(days=1)


def _previous_period_bounds(period_type: PeriodType, current_start: date) -> tuple[date, date]:
    """Return the inclusive start and end dates for the period immediately before the current one.

    Used to compute period-over-period deltas on the dashboard.

    Args:
        period_type: Granularity of the period.
        current_start: First day of the current period.

    Returns:
        Tuple of (start, end) dates for the previous period, both inclusive.
    """
    if period_type == "daily":
        prev = current_start - timedelta(days=1)
        return prev, prev
    if period_type == "all_time":
        return date(1999, 1, 1), date(1999, 1, 1)
    if period_type == "weekly":
        end = current_start - timedelta(days=1)
        return end - timedelta(days=6), end
    if period_type == "monthly":
        start = _add_months(current_start, -1)
        return start, current_start - timedelta(days=1)
    if period_type == "quarterly":
        start = _add_months(current_start, -3)
        return start, current_start - timedelta(days=1)
    start = current_start.replace(year=current_start.year - 1)
    return start, current_start - timedelta(days=1)


def _next_month(value: date) -> date:
    """Return the first day of the month following value."""
    return _add_months(value, 1)


def _add_months(value: date, months: int) -> date:
    """Return a new date shifted by the given number of months, always on the 1st.

    Args:
        value: Source date (day is ignored; result is always day=1).
        months: Number of months to add (may be negative).

    Returns:
        First day of the resulting month.
    """
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month, day=1)
