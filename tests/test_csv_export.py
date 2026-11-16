import csv
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from finance_core.errors import StorageError
from finance_core.models import Transaction
from finance_core.storage import CSV_COLUMNS, export_transactions_csv
from finance_core.transaction_service import TransactionService


def make(transaction_id, kind, amount, category, description, day="2026-11-12"):
    return Transaction(
        transaction_id, kind, Decimal(amount), category, description, date.fromisoformat(day)
    )


SAMPLE = [
    make("T0001", "income", "1500.00", "Salary", "November pay", "2026-11-01"),
    make("T0002", "expense", "12.50", "Food", "Lunch, with team"),
]


class CsvExportTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp_dir.cleanup)
        self.folder = Path(self._temp_dir.name)
        self.file = self.folder / "export.csv"

    def read_rows(self):
        with open(self.file, encoding="utf-8-sig", newline="") as file:
            return list(csv.reader(file))

    def test_header_and_rows_are_written(self):
        export_transactions_csv(self.file, SAMPLE)
        rows = self.read_rows()
        self.assertEqual(tuple(rows[0]), CSV_COLUMNS)
        self.assertEqual(rows[1], ["T0001", "income", "1500.00", "Salary", "November pay", "2026-11-01"])
        self.assertEqual(rows[2], ["T0002", "expense", "12.50", "Food", "Lunch, with team", "2026-11-12"])
        self.assertEqual(len(rows), 3)

    def test_commas_and_quotes_survive_a_round_trip(self):
        tricky = [make("T0001", "expense", "5.00", "Food", 'He said "hi", then left')]
        export_transactions_csv(self.file, tricky)
        self.assertEqual(self.read_rows()[1][4], 'He said "hi", then left')

    def test_amounts_entered_without_decimals_export_with_two_places(self):
        service = TransactionService()
        service.add_transaction("expense", "7", "Food", "Snack", "2026-11-12")
        export_transactions_csv(self.file, service.get_all_transactions())
        self.assertEqual(self.read_rows()[1][2], "7.00")

    def test_empty_export_has_only_the_header(self):
        export_transactions_csv(self.file, [])
        rows = self.read_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(tuple(rows[0]), CSV_COLUMNS)

    def test_file_has_a_byte_order_mark_for_excel(self):
        export_transactions_csv(self.file, SAMPLE)
        self.assertTrue(self.file.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_accented_characters_are_preserved(self):
        export_transactions_csv(self.file, [make("T0001", "expense", "3.00", "Café", "Crème brûlée")])
        row = self.read_rows()[1]
        self.assertEqual((row[3], row[4]), ("Café", "Crème brûlée"))

    def test_text_that_looks_like_a_formula_is_neutralised(self):
        dangerous = [
            make("T0001", "expense", "1.00", "Food", "=SUM(A1:A9)"),
            make("T0002", "expense", "1.00", "Food", "+1234"),
            make("T0003", "expense", "1.00", "Food", "-5 refund"),
            make("T0004", "expense", "1.00", "Food", "@cmd"),
        ]
        export_transactions_csv(self.file, dangerous)
        descriptions = [row[4] for row in self.read_rows()[1:]]
        self.assertEqual(descriptions, ["'=SUM(A1:A9)", "'+1234", "'-5 refund", "'@cmd"])

    def test_normal_text_is_not_changed(self):
        export_transactions_csv(self.file, [make("T0001", "expense", "1.00", "Food", "Lunch")])
        self.assertEqual(self.read_rows()[1][4], "Lunch")

    def test_existing_file_is_replaced_and_no_temp_files_remain(self):
        self.file.write_text("old content", encoding="utf-8")
        export_transactions_csv(self.file, SAMPLE)
        self.assertNotIn("old content", self.file.read_text(encoding="utf-8-sig"))
        self.assertEqual(list(self.folder.glob("*.tmp")), [])

    def test_missing_folder_is_created(self):
        nested = self.folder / "exports" / "all.csv"
        export_transactions_csv(nested, SAMPLE)
        self.assertTrue(nested.exists())

    def test_failure_raises_storage_error_and_leaves_no_temp_file(self):
        # A folder with the target's name makes the final replace step fail.
        blocker = self.folder / "blocked.csv"
        blocker.mkdir()
        with self.assertRaises(StorageError):
            export_transactions_csv(blocker, SAMPLE)
        self.assertEqual(list(self.folder.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()