"""Shared helper for the command-line tests (not a test file itself)."""

import tempfile
import unittest
from pathlib import Path

from cli.console import Console
from cli.context import AppContext
from finance_core.budget_service import BudgetService
from finance_core.storage import load_budgets, load_transactions
from finance_core.transaction_service import TransactionService


class CliTestCase(unittest.TestCase):
    """Gives each test a fresh temporary data folder and a scripted console.

    Call make_context("answer 1", "answer 2", ...) to get an AppContext
    whose prompts are answered, in order, from that list. Anything the
    program prints is collected in self.text.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        folder = Path(temp_dir.name)
        self.transactions_file = folder / "transactions.json"
        self.budgets_file = folder / "budgets.json"
        self.export_file = folder / "export.csv"
        self.lines: list[str] = []

    def make_context(self, *answers: str) -> AppContext:
        remaining = iter(answers)
        console = Console(
            input_func=lambda prompt="": next(remaining),
            output_func=self.lines.append,
        )
        return AppContext(
            console=console,
            transactions=TransactionService(load_transactions(self.transactions_file)),
            budgets=BudgetService(load_budgets(self.budgets_file)),
            transactions_file=self.transactions_file,
            budgets_file=self.budgets_file,
            export_file=self.export_file,
        )

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def saved_transactions(self):
        """What is actually on disk right now."""
        return load_transactions(self.transactions_file)

    def saved_budgets(self):
        return load_budgets(self.budgets_file)