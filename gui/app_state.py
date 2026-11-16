"""The data and the actions behind the graphical interface.

AppState owns the services, saves after every change and tells the
screens to refresh. It contains no widgets, so it can be tested without
a window. It uses the same finance_core services as the command-line
version, so both interfaces follow identical rules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from finance_core.analytics_service import month_key, transactions_in_month
from finance_core.budget_service import BudgetService
from finance_core.errors import ValidationError
from finance_core.models import Budget, Transaction
from finance_core.storage import (
    export_transactions_csv,
    load_budgets,
    load_transactions,
    save_budgets,
    save_transactions,
)
from finance_core.transaction_service import TransactionService

ALL_TIME = "All time"


class AppState:
    """Loads the saved files and applies every change safely.

    Creating an AppState raises StorageError if a data file is corrupted,
    before any window is shown, so a damaged file is never overwritten.
    """

    def __init__(self, transactions_file: Path, budgets_file: Path) -> None:
        self.transactions_file = Path(transactions_file)
        self.budgets_file = Path(budgets_file)
        self.transactions = TransactionService(load_transactions(self.transactions_file))
        self.budgets = BudgetService(load_budgets(self.budgets_file))
        self._listeners: list[Callable[[], None]] = []

    # ----- telling the screens that something changed -----

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    def _commit(self, save: Callable[[], None]) -> None:
        """Save, then refresh the screens even if saving failed.

        If saving fails the change is still in memory, so the screens must
        show it; the error then reaches the user and the next successful
        save writes everything.
        """
        try:
            save()
        finally:
            self.notify()

    # ----- transactions -----

    def add_transaction(self, **values: object) -> Transaction:
        transaction = self.transactions.add_transaction(**values)
        self._commit(self._save_transactions)
        return transaction

    def edit_transaction(self, transaction_id: str, **values: object) -> Transaction:
        transaction = self.transactions.edit_transaction(transaction_id, **values)
        self._commit(self._save_transactions)
        return transaction

    def delete_transaction(self, transaction_id: str) -> Transaction:
        transaction = self.transactions.delete_transaction(transaction_id)
        self._commit(self._save_transactions)
        return transaction

    # ----- budgets -----

    def create_budget(self, category: str, month: object, limit: object) -> Budget:
        budget = self.budgets.create_budget(category, month, limit)
        self._commit(self._save_budgets)
        return budget

    def edit_budget(self, category: str, month: object, limit: object) -> Budget:
        budget = self.budgets.edit_budget(category, month, limit)
        self._commit(self._save_budgets)
        return budget

    def delete_budget(self, category: str, month: object) -> Budget:
        budget = self.budgets.delete_budget(category, month)
        self._commit(self._save_budgets)
        return budget

    # ----- information for the screens -----

    def period_transactions(self, month: Optional[str]) -> list[Transaction]:
        """All transactions, or only those in one 'YYYY-MM' month."""
        everything = self.transactions.get_all_transactions()
        if month in (None, "", ALL_TIME):
            return everything
        return transactions_in_month(everything, month)

    def categories(self) -> list[str]:
        """Every category used by a transaction or a budget, A to Z."""
        names = {t.category for t in self.transactions.get_all_transactions()}
        names |= {b.category for b in self.budgets.get_all_budgets()}
        return sorted(names, key=str.lower)

    def months(self) -> list[str]:
        """Every month that has a transaction or a budget, newest first."""
        found = {month_key(t.transaction_date) for t in self.transactions.get_all_transactions()}
        found |= {b.month for b in self.budgets.get_all_budgets()}
        return sorted(found, reverse=True)

    # ----- export -----

    def is_data_file(self, path: Path) -> bool:
        """True if path is one of the program's own data files."""
        protected = {self.transactions_file.resolve(), self.budgets_file.resolve()}
        return Path(path).resolve() in protected

    def export_csv(self, path: Path) -> int:
        """Write all transactions to a CSV file and return how many were written."""
        path = Path(path)
        if self.is_data_file(path):
            raise ValidationError(
                "That file holds your saved data. Choose a different file name for the export."
            )
        transactions = self.transactions.get_all_transactions()
        export_transactions_csv(path, transactions)
        return len(transactions)

    # ----- saving -----

    def _save_transactions(self) -> None:
        save_transactions(self.transactions_file, self.transactions.get_all_transactions())

    def _save_budgets(self) -> None:
        save_budgets(self.budgets_file, self.budgets.get_all_budgets())