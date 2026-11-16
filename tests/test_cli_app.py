import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from cli.cli_interface import CommandLineApp
from finance_core.errors import StorageError
from finance_core.storage import load_budgets, load_transactions


class CommandLineAppTests(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        folder = Path(temp_dir.name)
        self.transactions_file = folder / "transactions.json"
        self.budgets_file = folder / "budgets.json"
        self.export_file = folder / "export.csv"

    def run_app(self, *answers) -> str:
        """Run a whole session with scripted answers and return everything printed."""
        remaining = iter(answers)
        lines = []
        app = CommandLineApp(
            self.transactions_file,
            self.budgets_file,
            self.export_file,
            input_func=lambda prompt="": next(remaining),
            output_func=lines.append,
        )
        app.run()
        return "\n".join(lines)

    def test_main_menu_lists_the_seven_required_options(self):
        text = self.run_app("7")
        for line in (
            "1. Transaction management",
            "2. Search and filtering",
            "3. Sorting",
            "4. Budget management",
            "5. Financial analytics",
            "6. Export records",
            "7. Exit",
        ):
            self.assertIn(line, text)
        self.assertIn("Goodbye!", text)

    def test_invalid_main_menu_choices_do_not_crash(self):
        text = self.run_app("0", "x", "8", "", "7")
        self.assertEqual(text.count("Invalid choice"), 4)
        self.assertIn("Goodbye!", text)

    def test_full_session_across_every_menu(self):
        text = self.run_app(
            # 1 Transactions: add income, add expense, view, back
            "1", "1", "2000", "Salary", "Pay", "2026-11-01",
            "2", "85", "Food", "Weekly shop", "2026-11-03",
            "3", "6",
            # 2 Search: category Food
            "2", "", "", "", "food", "", "", "",
            # 3 Sort by amount descending
            "3", "amount", "desc",
            # 4 Budgets: create Food 100 for November, view November, back
            "4", "1", "Food", "2026-11", "100",
            "2", "2026-11", "5",
            # 5 Analytics for November
            "5", "2026-11",
            # 6 Export to the default file
            "6", "",
            # 7 Exit
            "7",
        )
        self.assertIn("Added income T0001", text)
        self.assertIn("Added expense T0002", text)
        self.assertIn("1 transaction(s) found.", text)
        self.assertIn("Approaching limit", text)             # 85 of 100 spent
        self.assertIn("Net savings:          1,915.00", text)
        self.assertIn("Exported 2 transaction(s)", text)

        # What ended up on disk
        self.assertEqual(len(load_transactions(self.transactions_file)), 2)
        self.assertEqual(load_budgets(self.budgets_file)[0].limit, Decimal("100.00"))
        with open(self.export_file, encoding="utf-8-sig", newline="") as file:
            self.assertEqual(len(list(csv.reader(file))), 3)

    def test_data_persists_when_the_program_is_closed_and_reopened(self):
        self.run_app("1", "2", "9.99", "Food", "Coffee beans", "2026-11-12", "6", "7")
        text = self.run_app("1", "3", "6", "7")           # second run: view all
        self.assertIn("Coffee beans", text)
        self.assertIn("9.99", text)

    def test_budgets_persist_when_the_program_is_closed_and_reopened(self):
        self.run_app("4", "1", "Bills", "2026-12", "500", "5", "7")
        text = self.run_app("4", "2", "", "5", "7")
        self.assertIn("Bills", text)
        self.assertIn("500.00", text)

    def test_an_error_in_one_screen_returns_to_the_menu_and_the_session_continues(self):
        text = self.run_app("1", "4", "T9999", "6", "7")   # edit an ID that does not exist
        self.assertIn("Error: No transaction found with ID 'T9999'.", text)
        self.assertIn("Goodbye!", text)

    def test_cancel_returns_to_the_menu(self):
        text = self.run_app("1", "1", "10", "cancel", "6", "7")
        self.assertIn("Cancelled.", text)
        self.assertEqual(load_transactions(self.transactions_file), [])

    def test_input_ending_unexpectedly_is_handled(self):
        def ending_input(prompt=""):
            raise EOFError

        lines = []
        app = CommandLineApp(
            self.transactions_file, self.budgets_file, self.export_file,
            input_func=ending_input, output_func=lines.append,
        )
        app.run()
        self.assertIn("Input ended. Your data has already been saved.", "\n".join(lines))

    def test_keyboard_interrupt_is_handled(self):
        def interrupting_input(prompt=""):
            raise KeyboardInterrupt

        lines = []
        app = CommandLineApp(
            self.transactions_file, self.budgets_file, self.export_file,
            input_func=interrupting_input, output_func=lines.append,
        )
        app.run()
        self.assertIn("Input ended.", "\n".join(lines))


class CorruptedDataTests(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        folder = Path(temp_dir.name)
        self.transactions_file = folder / "transactions.json"
        self.budgets_file = folder / "budgets.json"
        self.export_file = folder / "export.csv"

    def test_corrupted_transaction_file_stops_startup_and_is_left_untouched(self):
        broken = '{"transactions": [ {"oops": '
        self.transactions_file.write_text(broken, encoding="utf-8")
        with self.assertRaises(StorageError):
            CommandLineApp(self.transactions_file, self.budgets_file, self.export_file)
        self.assertEqual(self.transactions_file.read_text(encoding="utf-8"), broken)

    def test_corrupted_budget_file_stops_startup_and_is_left_untouched(self):
        broken = "not json at all"
        self.budgets_file.write_text(broken, encoding="utf-8")
        with self.assertRaises(StorageError):
            CommandLineApp(self.transactions_file, self.budgets_file, self.export_file)
        self.assertEqual(self.budgets_file.read_text(encoding="utf-8"), broken)

    def test_empty_files_are_treated_as_a_fresh_start(self):
        self.transactions_file.write_text("", encoding="utf-8")
        self.budgets_file.write_text("   ", encoding="utf-8")
        lines = []
        remaining = iter(["1", "3", "6", "7"])
        app = CommandLineApp(
            self.transactions_file, self.budgets_file, self.export_file,
            input_func=lambda prompt="": next(remaining), output_func=lines.append,
        )
        app.run()
        self.assertIn("No transactions recorded yet.", "\n".join(lines))


if __name__ == "__main__":
    unittest.main()