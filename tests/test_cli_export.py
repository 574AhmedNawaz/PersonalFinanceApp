import csv
import unittest

from cli.export_commands import export_records
from tests.cli_support import CliTestCase


class ExportScreenTests(CliTestCase):
    def seed(self):
        context = self.make_context()
        context.transactions.add_transaction("income", "1500", "Salary", "Pay", "2026-11-01")
        context.transactions.add_transaction("expense", "12.50", "Food", "Lunch", "2026-11-05")
        context.save_transactions()

    def read_export(self, path=None):
        with open(path or self.export_file, encoding="utf-8-sig", newline="") as file:
            return list(csv.reader(file))

    def test_export_to_the_default_file(self):
        self.seed()
        export_records(self.make_context(""))
        rows = self.read_export()
        self.assertEqual(len(rows), 3)                       # header + 2 transactions
        self.assertEqual(rows[1][0], "T0001")
        self.assertIn("Exported 2 transaction(s)", self.text)

    def test_export_to_a_chosen_file_name(self):
        self.seed()
        chosen = self.export_file.parent / "my records.csv"
        export_records(self.make_context(f'"{chosen}"'))      # quotes are stripped
        self.assertEqual(len(self.read_export(chosen)), 3)

    def test_nothing_to_export(self):
        export_records(self.make_context())
        self.assertIn("There are no transactions to export.", self.text)
        self.assertFalse(self.export_file.exists())

    def test_existing_file_is_not_overwritten_without_permission(self):
        self.seed()
        self.export_file.write_text("precious old export", encoding="utf-8")
        export_records(self.make_context("", "n"))
        self.assertIn("Export cancelled", self.text)
        self.assertEqual(self.export_file.read_text(encoding="utf-8"), "precious old export")

    def test_existing_file_is_replaced_when_the_user_agrees(self):
        self.seed()
        self.export_file.write_text("old", encoding="utf-8")
        export_records(self.make_context("", "y"))
        self.assertEqual(len(self.read_export()), 3)

    def test_exporting_over_the_data_file_is_refused(self):
        self.seed()
        before = self.transactions_file.read_text(encoding="utf-8")
        context = self.make_context(str(self.transactions_file))
        context.console.run_action(lambda: export_records(context))
        self.assertIn("That file holds your saved data", self.text)
        self.assertEqual(self.transactions_file.read_text(encoding="utf-8"), before)

    def test_a_write_failure_is_reported_as_an_error_message(self):
        self.seed()
        blocker = self.export_file.parent / "folder.csv"
        blocker.mkdir()
        context = self.make_context(str(blocker), "y")   # exists, so confirm; then writing fails
        context.console.run_action(lambda: export_records(context))
        self.assertIn("Error: Could not save data", self.text)


if __name__ == "__main__":
    unittest.main()