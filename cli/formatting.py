"""Plain-text formatting for the command-line interface.

These functions only turn data into text. No financial calculations
happen here; those all live in finance_core.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Optional, Sequence

from finance_core.analytics_service import MonthlySummary
from finance_core.budget_service import BudgetStatus
from finance_core.models import Transaction

DESCRIPTION_WIDTH = 30
CATEGORY_WIDTH = 20


def format_money(amount: Decimal) -> str:
    """1234.5 -> '1,234.50'."""
    return f"{amount:,.2f}"


def format_percent(value: Optional[Decimal], missing: str = "N/A") -> str:
    """Decimal('80') -> '80.00%'; None -> the `missing` text."""
    if value is None:
        return missing
    return f"{value:,.2f}%"


def _shorten(text: str, width: int) -> str:
    """Collapse line breaks and cut long text so tables stay aligned."""
    text = " ".join(text.split())
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."


def format_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    right_aligned: Sequence[int] = (),
) -> str:
    """Lay out rows in aligned columns under a header and a dashed line.

    Columns listed in right_aligned (by position) are right-aligned,
    which keeps the digits of numbers lined up.
    """
    widths = [len(header) for header in headers]
    for row in rows:
        for position, cell in enumerate(row):
            widths[position] = max(widths[position], len(cell))

    def render(cells: Sequence[str]) -> str:
        parts = [
            cell.rjust(widths[position])
            if position in right_aligned
            else cell.ljust(widths[position])
            for position, cell in enumerate(cells)
        ]
        return "  ".join(parts).rstrip()

    lines = [render(headers), "  ".join("-" * width for width in widths)]
    lines.extend(render(row) for row in rows)
    return "\n".join(lines)


def transactions_table(transactions: Iterable[Transaction]) -> str:
    rows = [
        [
            t.transaction_id,
            t.transaction_date.isoformat(),
            t.transaction_type,
            _shorten(t.category, CATEGORY_WIDTH),
            _shorten(t.description, DESCRIPTION_WIDTH),
            format_money(t.amount),
        ]
        for t in transactions
    ]
    headers = ("ID", "Date", "Type", "Category", "Description", "Amount")
    return format_table(headers, rows, right_aligned=(5,))


def budgets_table(statuses: Iterable[BudgetStatus]) -> str:
    rows = [
        [
            _shorten(s.category, CATEGORY_WIDTH),
            s.month,
            format_money(s.limit),
            format_money(s.spent),
            format_money(s.remaining),
            format_percent(s.utilisation_percent),
            s.status,
        ]
        for s in statuses
    ]
    headers = ("Category", "Month", "Budget", "Spent", "Remaining", "Used", "Status")
    return format_table(headers, rows, right_aligned=(2, 3, 4, 5))


def category_totals_table(totals: dict[str, Decimal]) -> str:
    rows = [
        [_shorten(category, CATEGORY_WIDTH), format_money(total)]
        for category, total in totals.items()
    ]
    return format_table(("Category", "Spent"), rows, right_aligned=(1,))


def monthly_table(months: Iterable[MonthlySummary]) -> str:
    rows = [
        [m.month, format_money(m.income), format_money(m.expenses), format_money(m.net)]
        for m in months
    ]
    return format_table(("Month", "Income", "Expenses", "Net"), rows, right_aligned=(1, 2, 3))