"""Data models for the Personal Finance application."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

INCOME = "income"
EXPENSE = "expense"
TRANSACTION_TYPES = (INCOME, EXPENSE)


@dataclass(frozen=True)
class Transaction:
    """A single income or expense record.

    The amount is always positive; the transaction type says whether it is
    money coming in or going out. The class is frozen (immutable) so a
    transaction can only change through TransactionService, which validates
    every edit.
    """

    transaction_id: str
    transaction_type: str
    amount: Decimal
    category: str
    description: str
    transaction_date: date

    def to_dict(self) -> dict[str, str]:
        """Convert to a JSON-friendly dictionary.

        The amount is stored as text because JSON numbers are floats,
        which would reintroduce rounding errors.
        """
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type,
            "amount": str(self.amount),
            "category": self.category,
            "description": self.description,
            "date": self.transaction_date.isoformat(),
        }

@dataclass(frozen=True)
class Budget:
    """A spending limit for one expense category in one month.

    The month is stored as text in 'YYYY-MM' form, e.g. '2026-11'.
    """

    category: str
    month: str
    limit: Decimal

    def to_dict(self) -> dict[str, str]:
        """Convert to a JSON-friendly dictionary (limit stored as text)."""
        return {
            "category": self.category,
            "month": self.month,
            "limit": str(self.limit),
        }