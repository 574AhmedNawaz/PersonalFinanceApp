"""Financial analytics.

Every function takes a list of transactions and returns a result. To
report on a particular period (for example one month), the caller first
selects those transactions (see transaction_search) and passes them in.
That way every figure on a screen is calculated from the same set of
transactions, so the numbers always agree with each other.

Calculation rules:
- Total income / expenses: sum of the amounts of each transaction type.
- Net savings = total income - total expenses (can be negative).
- Savings rate = net savings / total income x 100, rounded to 2 places.
  It is None (not a number) when there is no income, never a divide by zero.
- Average expense = total expenses / number of expense transactions.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional

from finance_core.models import EXPENSE, INCOME, Transaction

ZERO = Decimal("0.00")
TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True)
class FinancialSummary:
    """The headline figures for a set of transactions."""

    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    savings_rate: Optional[Decimal]  # percent, or None when income is zero
    average_expense: Decimal
    transaction_count: int


@dataclass(frozen=True)
class MonthlySummary:
    """Income, expenses and net result for one calendar month."""

    month: str  # "YYYY-MM"
    income: Decimal
    expenses: Decimal

    @property
    def net(self) -> Decimal:
        return self.income - self.expenses


def month_key(day: date) -> str:
    """Return the month of a date as 'YYYY-MM', e.g. '2026-11'."""
    return day.strftime("%Y-%m")


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def total_by_type(transactions: Iterable[Transaction], transaction_type: str) -> Decimal:
    """Sum of the amounts of all transactions of one type."""
    total = sum(
        (t.amount for t in transactions if t.transaction_type == transaction_type),
        start=ZERO,
    )
    return total


def total_income(transactions: Iterable[Transaction]) -> Decimal:
    return total_by_type(transactions, INCOME)


def total_expenses(transactions: Iterable[Transaction]) -> Decimal:
    return total_by_type(transactions, EXPENSE)


def net_savings(transactions: Iterable[Transaction]) -> Decimal:
    transactions = list(transactions)
    return total_income(transactions) - total_expenses(transactions)


def savings_rate(transactions: Iterable[Transaction]) -> Optional[Decimal]:
    """Net savings as a percentage of income, or None if there is no income."""
    transactions = list(transactions)
    income = total_income(transactions)
    if income == 0:
        return None
    return _money(net_savings(transactions) / income * 100)


def average_expense(transactions: Iterable[Transaction]) -> Decimal:
    """Average amount of one expense transaction (0.00 if there are none)."""
    expenses = [t.amount for t in transactions if t.transaction_type == EXPENSE]
    if not expenses:
        return ZERO
    return _money(sum(expenses, start=ZERO) / len(expenses))


def expense_by_category(transactions: Iterable[Transaction]) -> dict[str, Decimal]:
    """Total expenses per category, largest first (ties in name order).

    A dictionary is used to add up each category in a single pass over
    the data, which is O(n).
    """
    totals: dict[str, Decimal] = {}
    for t in transactions:
        if t.transaction_type == EXPENSE:
            totals[t.category] = totals.get(t.category, ZERO) + t.amount
    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return dict(ordered)


def expense_by_category_and_month(
    transactions: Iterable[Transaction],
) -> dict[tuple[str, str], Decimal]:
    """Total expenses for every (category, 'YYYY-MM') pair.

    Budgets use this to compare actual spending with each limit.
    """
    totals: dict[tuple[str, str], Decimal] = {}
    for t in transactions:
        if t.transaction_type == EXPENSE:
            key = (t.category, month_key(t.transaction_date))
            totals[key] = totals.get(key, ZERO) + t.amount
    return totals


def monthly_summaries(transactions: Iterable[Transaction]) -> list[MonthlySummary]:
    """Income and expenses for each month that has transactions, oldest first."""
    income: dict[str, Decimal] = {}
    expenses: dict[str, Decimal] = {}
    for t in transactions:
        month = month_key(t.transaction_date)
        target = income if t.transaction_type == INCOME else expenses
        target[month] = target.get(month, ZERO) + t.amount
    months = sorted(set(income) | set(expenses))  # a set merges the two month lists
    return [
        MonthlySummary(month, income.get(month, ZERO), expenses.get(month, ZERO))
        for month in months
    ]


def highest_expense_category(
    transactions: Iterable[Transaction],
) -> Optional[tuple[str, Decimal]]:
    """The (category, total) with the largest spending, or None if no expenses.

    If two categories tie, the one that comes first alphabetically wins.
    """
    totals = expense_by_category(transactions)
    if not totals:
        return None
    category = next(iter(totals))  # expense_by_category is already sorted
    return category, totals[category]


def top_transactions(
    transactions: Iterable[Transaction],
    count: int = 5,
    transaction_type: Optional[str] = None,
) -> list[Transaction]:
    """The highest-value transactions, largest first.

    Optionally restricted to one type. heapq.nlargest keeps only the best
    `count` items, O(n log k), instead of sorting everything.
    """
    if count < 1:
        return []
    candidates = (
        t
        for t in transactions
        if transaction_type is None or t.transaction_type == transaction_type
    )
    return heapq.nlargest(count, candidates, key=lambda t: t.amount)


def summarise(transactions: Iterable[Transaction]) -> FinancialSummary:
    """All headline figures for the given transactions in one call."""
    transactions = list(transactions)
    return FinancialSummary(
        total_income=total_income(transactions),
        total_expenses=total_expenses(transactions),
        net_savings=net_savings(transactions),
        savings_rate=savings_rate(transactions),
        average_expense=average_expense(transactions),
        transaction_count=len(transactions),
    )