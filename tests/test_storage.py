import json
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from finance_core.errors import StorageError
from finance_core.models import Transaction
from finance_core.storage import load_transactions, save_transactions


def sample_transactions() -> list[Transaction]:
    return [
        Transaction("T0001", "income", Decimal("1500.00"), "Salary", "Pay", date(2026, 11, 1)),
        Transaction("T0002", "expense", Decimal("12.50"), "Food", "Lunch", date(2026, 11, 12)),
    ]


class StorageTests(unittest.TestCase):
    def setUp(self):
        # A fresh temporary folder per test: real data is never touched.
        self._temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp_dir.cleanup)
        self.folder = Path(self._temp_dir.name)
        self.file = self.folder / "transactions.json"

    def write_raw(self, text: str) -> None:
        self.file.write_text(text, encoding="utf-8")

    # ----- saving and loading -----

    def test_round_trip_preserves_every_field(self):
        original = sample_transactions()
        save_transactions(self.file, original)
        self.assertEqual(load_transactions(self.file), original)

    def test_amounts_are_saved_as_text_not_floats(self):
        save_transactions(self.file, sample_transactions())
        data = json.loads(self.file.read_text(encoding="utf-8"))
        self.assertEqual(data["transactions"][1]["amount"], "12.50")

    def test_save_creates_missing_folder(self):
        nested = self.folder / "new" / "data.json"
        save_transactions(nested, sample_transactions())
        self.assertTrue(nested.exists())

    def test_save_replaces_old_content_and_leaves_no_temp_files(self):
        save_transactions(self.file, sample_transactions())
        save_transactions(self.file, sample_transactions()[:1])
        self.assertEqual(len(load_transactions(self.file)), 1)
        self.assertEqual(list(self.folder.glob("*.tmp")), [])

    def test_saving_empty_list_round_trips(self):
        save_transactions(self.file, [])
        self.assertEqual(load_transactions(self.file), [])

    # ----- missing / empty / corrupt files -----

    def test_missing_file_gives_empty_list(self):
        self.assertEqual(load_transactions(self.folder / "nope.json"), [])

    def test_empty_file_gives_empty_list(self):
        self.write_raw("")
        self.assertEqual(load_transactions(self.file), [])
        self.write_raw("   \n  ")
        self.assertEqual(load_transactions(self.file), [])

    def test_malformed_json_raises_and_file_is_untouched(self):
        broken = '{"version": 1, "transactions": [ {"oops": '
        self.write_raw(broken)
        with self.assertRaises(StorageError) as context:
            load_transactions(self.file)
        self.assertIn("not valid JSON", str(context.exception))
        self.assertEqual(self.file.read_text(encoding="utf-8"), broken)

    def test_wrong_structure_raises(self):
        for text in ["[]", '"hello"', '{"version": 1}', '{"transactions": "no"}']:
            with self.subTest(text=text):
                self.write_raw(text)
                with self.assertRaises(StorageError):
                    load_transactions(self.file)

    def test_record_with_missing_field_raises(self):
        record = sample_transactions()[0].to_dict()
        del record["category"]
        self.write_raw(json.dumps({"transactions": [record]}))
        with self.assertRaises(StorageError) as context:
            load_transactions(self.file)
        self.assertIn("Record 1", str(context.exception))

    def test_record_with_invalid_value_raises(self):
        record = sample_transactions()[0].to_dict()
        record["amount"] = "-5"
        self.write_raw(json.dumps({"transactions": [record]}))
        with self.assertRaises(StorageError):
            load_transactions(self.file)

    def test_non_object_record_raises(self):
        self.write_raw(json.dumps({"transactions": ["not a record"]}))
        with self.assertRaises(StorageError):
            load_transactions(self.file)

    def test_duplicate_ids_in_file_raise(self):
        record = sample_transactions()[0].to_dict()
        self.write_raw(json.dumps({"transactions": [record, record]}))
        with self.assertRaises(StorageError) as context:
            load_transactions(self.file)
        self.assertIn("duplicate", str(context.exception))


if __name__ == "__main__":
    unittest.main()