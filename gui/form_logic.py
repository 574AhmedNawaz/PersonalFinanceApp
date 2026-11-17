"""Checking what the user typed into the graphical forms.

Each field is checked on its own so every problem can be shown next to
its field at once, instead of one error at a time. The checks reuse the
core validators, so the GUI accepts and rejects exactly what the CLI does.
No widgets are used here, which keeps this module easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional

from finance_core.errors import ValidationError
from finance_core.validation import (
    validate_amount,
    validate_category,
    validate_date,
    validate_month,
    validate_text,
    validate_transaction_type,
)

ANY = "All"  # the 'no filter' choice shown in drop-down lists


@dataclass
class FormResult:
    """The cleaned values, plus a message for every field that was wrong."""

    values: dict[str, object] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def check(self, name: str, validator: Callable[[object], object], raw: object) -> None:
        try:
            self.values[name] = validator(raw)
        except ValidationError as error:
            self.errors[name] = str(error)


def _description(value: object) -> str:
    return validate_text(value, "Description")


def _blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def check_transaction_form(
    transaction_type: object,
    amount: object,
    category: object,
    description: object,
    transaction_date: object,
    today: Optional[date] = None,
) -> FormResult:
    """Validate the add/edit transaction form. A blank date means today."""
    result = FormResult()
    result.check("transaction_type", validate_transaction_type, transaction_type)
    result.check("amount", validate_amount, amount)
    result.check("category", validate_category, category)
    result.check("description", _description, description)
    if _blank(transaction_date):
        result.values["transaction_date"] = today or date.today()
    else:
        result.check("transaction_date", validate_date, transaction_date)
    return result


def check_budget_form(category: object, month: object, limit: object) -> FormResult:
    """Validate the add/edit budget form."""
    result = FormResult()
    result.check("category", validate_category, category)
    result.check("month", validate_month, month)
    result.check("limit", validate_amount, limit)
    return result


def check_filter_form(
    text: object,
    transaction_type: object,
    category: object,
    start_date: object,
    end_date: object,
) -> FormResult:
    """Validate the filter bar above the transaction list.

    Blank fields (and 'All' for the type) mean 'do not filter on this',
    so those values come back as None.
    """
    result = FormResult()
    result.values["text"] = None if _blank(text) else str(text).strip()

    if _blank(transaction_type) or str(transaction_type).strip() == ANY:
        result.values["transaction_type"] = None
    else:
        result.check("transaction_type", validate_transaction_type, transaction_type)

    if _blank(category):
        result.values["category"] = None
    else:
        result.check("category", validate_category, category)

    for name, raw in (("start_date", start_date), ("end_date", end_date)):
        if _blank(raw):
            result.values[name] = None
        else:
            result.check(name, validate_date, raw)

    start, end = result.values.get("start_date"), result.values.get("end_date")
    if start is not None and end is not None and start > end:
        result.errors["end_date"] = "The end date cannot be before the start date."
    return result