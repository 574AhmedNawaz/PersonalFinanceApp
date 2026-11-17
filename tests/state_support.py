"""Shared helper for the graphical-interface tests (not a test file itself)."""

import tempfile
import unittest
from pathlib import Path

from gui.app_state import AppState


class StateTestCase(unittest.TestCase):
    """Gives each test its own temporary data folder and a fresh AppState."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.folder = Path(temp_dir.name)
        self.transactions_file = self.folder / "transactions.json"
        self.budgets_file = self.folder / "budgets.json"
        self.state = AppState(self.transactions_file, self.budgets_file)

    def add(self, kind, amount, category, description, day):
        return self.state.add_transaction(
            transaction_type=kind, amount=amount, category=category,
            description=description, transaction_date=day,
        )