"""Searching, filtering and sorting of transactions.

These are plain functions that take a list of transactions and return a
new list. They never change the stored data, so the CLI and GUI can
search, then sort the results, then display them.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable, Optional

from finance_core.errors import ValidationError
from finance_core.models import Transaction
from finance_core.validation import (
    validate_category,
    validate_date,
    validate_transaction_type,
)


def _is_blank(value: object) -> bool:
    """True for None or empty text, so GUI form fields left empty count as 'not used'."""
    return value is None or str(value).strip() == ""


def search_transactions(
    transactions: Iterable[Transaction],
    *,
    transaction_id: Optional[str] = None,
    text: Optional[str] = None,
    transaction_type: Optional[str] = None,
    category: Optional[str] = None,
    on_date: Optional[object] = None,
    start_date: Optional[object] = None,
    end_date: Optional[object] = None,
) -> list[Transaction]:
    """Return the transactions that match ALL of the supplied criteria.

    Criteria left as None or empty text are ignored.
    - transaction_id: exact match (case-insensitive)
    - text: case-insensitive substring of the description
    - transaction_type: 'income' or 'expense'
    - category: case-insensitive exact match
    - on_date: a single day
    - start_date / end_date: inclusive range; either end may be left open

    An empty result is not an error: the caller decides what to show.
    Cost is O(n): every transaction is checked once.
    """
    wanted_id = None if _is_blank(transaction_id) else str(transaction_id).strip().upper()
    wanted_text = None if _is_blank(text) else str(text).strip().lower()
    wanted_type = None if _is_blank(transaction_type) else validate_transaction_type(transaction_type)
    wanted_category = None if _is_blank(category) else validate_category(category)
    day = None if _is_blank(on_date) else validate_date(on_date)
    start = None if _is_blank(start_date) else validate_date(start_date)
    end = None if _is_blank(end_date) else validate_date(end_date)

    if day is not None and (start is not None or end is not None):
        raise ValidationError("Use either a single date or a date range, not both.")
    if start is not None and end is not None and start > end:
        raise ValidationError("The start date cannot be after the end date.")

    if day is not None:
        start = end = day  # a single day is just a range of one day

    return [
        t
        for t in transactions
        if _matches(t, wanted_id, wanted_text, wanted_type, wanted_category, start, end)
    ]


def _matches(
    transaction: Transaction,
    wanted_id: Optional[str],
    wanted_text: Optional[str],
    wanted_type: Optional[str],
    wanted_category: Optional[str],
    start: Optional[date],
    end: Optional[date],
) -> bool:
    if wanted_id is not None and transaction.transaction_id.upper() != wanted_id:
        return False
    if wanted_text is not None and wanted_text not in transaction.description.lower():
        return False
    if wanted_type is not None and transaction.transaction_type != wanted_type:
        return False
    if wanted_category is not None and transaction.category != wanted_category:
        return False
    if start is not None and transaction.transaction_date < start:
        return False
    if end is not None and transaction.transaction_date > end:
        return False
    return True