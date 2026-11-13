"""Monthly budget management.

A budget is a spending limit for one expense category in one month.
Only expense transactions count towards spending; income never does.

Budget status rules (utilisation = spent / limit):
- Within budget:      below 80% of the limit
- Approaching limit:  80% or more, but below the limit
- Fully used:         spent exactly equals the limit
- Exceeded:           spent is more than the limit
The comparisons use exact Decimal amounts, not the rounded percentage
shown to the user, so a budget at 99.999% is never reported as "Fully used".
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional

from finance_core.analytics_service import ZERO, expense_by_category_and_month
from finance_core.errors import BudgetNotFoundError, ValidationError
from finance_core.models import Budget, Transaction
from finance_core.validation import validate_amount, validate_category, validate_month

APPROACHING_PERCENT = Decimal("80")

WITHIN_BUDGET = "Within budget"
APPROACHING_LIMIT = "Approaching limit"
FULLY_USED = "Fully used"
EXCEEDED = "Exceeded"


@dataclass(frozen=True)
class BudgetStatus:
    """A budget compared with what was actually spent."""

    category: str
    month: str
    limit: Decimal
    spent: Decimal
    remaining: Decimal  # negative when the budget is exceeded
    utilisation_percent: Decimal
    status: str


def classify_spending(spent: Decimal, limit: Decimal) -> str:
    """Apply the status rules described at the top of this module."""
    if spent > limit:
        return EXCEEDED
    if spent == limit:
        return FULLY_USED
    if spent * 100 >= limit * APPROACHING_PERCENT:
        return APPROACHING_LIMIT
    return WITHIN_BUDGET


class BudgetService:
    """Stores budgets and compares them with spending.

    Budgets are kept in a dictionary keyed by (category, month), which
    guarantees one budget per category per month and gives O(1) lookup.
    """

    def __init__(self, budgets: Iterable[Budget] = ()) -> None:
        self._budgets: dict[tuple[str, str], Budget] = {}
        for budget in budgets:
            key = (budget.category, budget.month)
            if key in self._budgets:
                raise ValidationError(
                    f"Duplicate budget for {budget.category} in {budget.month}."
                )
            self._budgets[key] = budget

    def __len__(self) -> int:
        return len(self._budgets)

    # ----- create / read / update / delete -----

    def create_budget(self, category: str, month: object, limit: object) -> Budget:
        """Create a budget. Fails if one already exists for that category and month."""
        budget = Budget(
            category=validate_category(category),
            month=validate_month(month),
            limit=validate_amount(limit),
        )
        key = (budget.category, budget.month)
        if key in self._budgets:
            raise ValidationError(
                f"A budget for {budget.category} in {budget.month} already exists. "
                "Edit it instead."
            )
        self._budgets[key] = budget
        return budget

    def get_budget(self, category: str, month: object) -> Budget:
        key = (validate_category(category), validate_month(month))
        try:
            return self._budgets[key]
        except KeyError:
            raise BudgetNotFoundError(
                f"No budget found for {key[0]} in {key[1]}."
            ) from None

    def get_all_budgets(self, month: Optional[object] = None) -> list[Budget]:
        """All budgets ordered by month then category, optionally for one month."""
        wanted_month = None if month in (None, "") else validate_month(month)
        budgets = [
            b for b in self._budgets.values() if wanted_month in (None, b.month)
        ]
        return sorted(budgets, key=lambda b: (b.month, b.category))

    def edit_budget(self, category: str, month: object, new_limit: object) -> Budget:
        """Change the limit of an existing budget.

        The category and month identify the budget, so they cannot be
        edited; delete the budget and create a new one to move it.
        """
        current = self.get_budget(category, month)
        updated = Budget(current.category, current.month, validate_amount(new_limit))
        self._budgets[(updated.category, updated.month)] = updated
        return updated

    def delete_budget(self, category: str, month: object) -> Budget:
        removed = self.get_budget(category, month)
        del self._budgets[(removed.category, removed.month)]
        return removed

    # ----- comparison with spending -----

    def get_statuses(
        self,
        transactions: Iterable[Transaction],
        month: Optional[object] = None,
    ) -> list[BudgetStatus]:
        """Compare every budget (optionally for one month) with actual spending.

        Spending is totalled once for all budgets, so the cost is
        O(transactions + budgets) rather than rescanning the transactions
        for each budget.
        """
        spending = expense_by_category_and_month(transactions)
        return [
            self._build_status(budget, spending.get((budget.category, budget.month), ZERO))
            for budget in self.get_all_budgets(month)
        ]

    @staticmethod
    def _build_status(budget: Budget, spent: Decimal) -> BudgetStatus:
        percent = (spent / budget.limit * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return BudgetStatus(
            category=budget.category,
            month=budget.month,
            limit=budget.limit,
            spent=spent,
            remaining=budget.limit - spent,
            utilisation_percent=percent,
            status=classify_spending(spent, budget.limit),
        )