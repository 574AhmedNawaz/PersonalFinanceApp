"""Turning money and percentages into text.

Both the command-line and the graphical interface show amounts the same
way, so the rule lives here once. These functions only format; no
financial calculations happen in them.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional


def format_money(amount: Decimal) -> str:
    """1234.5 -> '1,234.50'."""
    return f"{amount:,.2f}"


def format_percent(value: Optional[Decimal], missing: str = "N/A") -> str:
    """Decimal('80') -> '80.00%'; None -> the `missing` text."""
    if value is None:
        return missing
    return f"{value:,.2f}%"