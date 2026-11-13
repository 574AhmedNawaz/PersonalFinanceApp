import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finance_core.errors import StorageError
from finance_core.models import Budget
from finance_core.storage import load_budgets, save_budgets


def sample_budgets() -> list[Budget]:
    return [
        Budget("Food", "2026-11", Decimal("300.00")),
        Budget("Bills", "2026-11", Decimal("450.50")),
    ]


class BudgetStorageTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp_dir.cleanup)
        self.folder = Path(self._temp_dir.name)
        self.file = self.folder / "budgets.json"

    def write_raw(self, text: str) -> None:
        self.file.write_text(text, encoding="utf-8")

    def test_round_trip(self):
        save_budgets(self.file, sample_budgets())
        self.assertEqual(load_budgets(self.file), sample_budgets())

    def test_limits_are_saved_as_text(self):
        save_budgets(self.file, sample_budgets())
        data = json.loads(self.file.read_text(encoding="utf-8"))
        self.assertEqual(data["budgets"][1]["limit"], "450.50")

    def test_missing_and_empty_files_give_empty_list(self):
        self.assertEqual(load_budgets(self.folder / "nope.json"), [])
        self.write_raw("")
        self.assertEqual(load_budgets(self.file), [])

    def test_malformed_json_raises_and_file_is_untouched(self):
        broken = '{"budgets": ['
        self.write_raw(broken)
        with self.assertRaises(StorageError):
            load_budgets(self.file)
        self.assertEqual(self.file.read_text(encoding="utf-8"), broken)

    def test_wrong_structure_raises(self):
        for text in ["[]", '{"budgets": "no"}', '{"transactions": []}']:
            with self.subTest(text=text):
                self.write_raw(text)
                with self.assertRaises(StorageError):
                    load_budgets(self.file)

    def test_invalid_record_values_raise(self):
        good = sample_budgets()[0].to_dict()
        bad_records = [
            {**good, "limit": "-5"},
            {**good, "month": "2026-13"},
            {**good, "category": ""},
            {key: value for key, value in good.items() if key != "month"},
            "not a record",
        ]
        for record in bad_records:
            with self.subTest(record=record):
                self.write_raw(json.dumps({"budgets": [record]}))
                with self.assertRaises(StorageError):
                    load_budgets(self.file)

    def test_duplicate_budgets_raise(self):
        record = sample_budgets()[0].to_dict()
        self.write_raw(json.dumps({"budgets": [record, record]}))
        with self.assertRaises(StorageError) as context:
            load_budgets(self.file)
        self.assertIn("duplicate", str(context.exception))

    def test_save_leaves_no_temp_files(self):
        save_budgets(self.file, sample_budgets())
        save_budgets(self.file, sample_budgets()[:1])
        self.assertEqual(len(load_budgets(self.file)), 1)
        self.assertEqual(list(self.folder.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()