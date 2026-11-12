"""Reusable input validation shared by the CLI and the GUI.

Each function takes raw user input, checks it, and returns a clean value
of the correct type. Any problem raises ValidationError with a message
that is safe to show directly to the user.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from finance_core.errors import ValidationError
from finance_core.models import TRANSACTION_TYPES

DATE_FORMAT = "%Y-%m-%d"
MAX_AMOUNT = Decimal("1000000000")  # one billion: catches typing mistakes
MAX_TEXT_LENGTH = 100
TWO_PLACES = Decimal("0.01")


def validate_amount(value: object) -> Decimal:
    """Return a positive Decimal with at most two decimal places."""
    text = str(value).strip()
    if not text:
        raise ValidationError("Amount cannot be empty.")
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise ValidationError(f"'{text}' is not a valid amount.") from None
    if not amount.is_finite():
        raise ValidationError(f"'{text}' is not a valid amount.")
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if amount > MAX_AMOUNT:
        raise ValidationError(f"Amount cannot exceed {MAX_AMOUNT:,}.")
    if amount != amount.quantize(TWO_PLACES):
        raise ValidationError("Amount can have at most two decimal places.")
    return amount.quantize(TWO_PLACES)


def validate_date(value: object) -> date:
    """Return a date from a date object or a YYYY-MM-DD string."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    try:
        return datetime.strptime(text, DATE_FORMAT).date()
    except ValueError:
        raise ValidationError(
            f"'{text}' is not a valid date. Use YYYY-MM-DD, e.g. 2026-11-12."
        ) from None


def validate_transaction_type(value: object) -> str:
    """Return 'income' or 'expense' (case-insensitive input accepted)."""
    text = str(value).strip().lower()
    if text not in TRANSACTION_TYPES:
        raise ValidationError("Transaction type must be 'income' or 'expense'.")
    return text


def validate_text(value: object, field_name: str) -> str:
    """Return stripped, non-empty text no longer than MAX_TEXT_LENGTH."""
    text = str(value).strip()
    if not text:
        raise ValidationError(f"{field_name} cannot be empty.")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValidationError(
            f"{field_name} cannot be longer than {MAX_TEXT_LENGTH} characters."
        )
    return text


def validate_category(value: object) -> str:
    """Validate a category and normalise its capitalisation.

    'food', 'FOOD' and ' Food ' all become 'Food', so category totals are
    not split across spelling variants.
    """
    return validate_text(value, "Category").title()