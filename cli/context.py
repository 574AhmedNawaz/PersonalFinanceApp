"""The shared state that every command-line screen works with."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cli.console import Console
from finance_core.budget_service import BudgetService
from finance_core.storage import save_budgets, save_transactions
from finance_core.transaction_service import TransactionService


@dataclass
class AppContext:
    """Everything a screen needs: how to talk to the user, the data, the files.

    Each screen is a function that takes an AppContext, so screens never
    create their own services and the whole program shares one set of data.
    """

    console: Console
    transactions: TransactionService
    budgets: BudgetService
    transactions_file: Path
    budgets_file: Path
    export_file: Path

    def save_transactions(self) -> None:
        save_transactions(self.transactions_file, self.transactions.get_all_transactions())

    def save_budgets(self) -> None:
        save_budgets(self.budgets_file, self.budgets.get_all_budgets())