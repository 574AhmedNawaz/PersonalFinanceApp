import unittest
from decimal import Decimal
from unittest import mock

from finance_core.errors import StorageError, ValidationError
from finance_core.storage import load_budgets, load_transactions
from gui.app_state import ALL_TIME, AppState
from tests.state_support import StateTestCase


class ChangesAreSavedTests(StateTestCase):
    def test_adding_saves_to_disk_immediately(self):
        self.add("expense", "12.50", "Food", "Lunch", "2026-11-12")
        saved = load_transactions(self.transactions_file)
        self.assertEqual([(t.transaction_id, t.amount) for t in saved], [("T0001", Decimal("12.50"))])

    def test_editing_and_deleting_are_saved(self):
        self.add("expense", "12.50", "Food", "Lunch", "2026-11-12")
        self.state.edit_transaction("T0001", amount="20")
        self.assertEqual(load_transactions(self.transactions_file)[0].amount, Decimal("20.00"))
        self.state.delete_transaction("T0001")
        self.assertEqual(load_transactions(self.transactions_file), [])

    def test_budget_changes_are_saved(self):
        self.state.create_budget("Food", "2026-11", "300")
        self.state.edit_budget("Food", "2026-11", "450")
        self.assertEqual(load_budgets(self.budgets_file)[0].limit, Decimal("450.00"))
        self.state.delete_budget("Food", "2026-11")
        self.assertEqual(load_budgets(self.budgets_file), [])

    def test_invalid_data_is_rejected_and_nothing_is_saved(self):
        with self.assertRaises(ValidationError):
            self.add("expense", "-5", "Food", "Lunch", "2026-11-12")
        self.assertFalse(self.transactions_file.exists())

    def test_a_new_state_reads_back_what_was_saved(self):
        self.add("income", "100", "Gift", "Present", "2026-11-12")
        self.state.create_budget("Food", "2026-11", "50")
        again = AppState(self.transactions_file, self.budgets_file)
        self.assertEqual(len(again.transactions), 1)
        self.assertEqual(len(again.budgets), 1)

    def test_a_corrupted_file_stops_start_up_and_is_left_untouched(self):
        self.transactions_file.write_text("{not json", encoding="utf-8")
        with self.assertRaises(StorageError):
            AppState(self.transactions_file, self.budgets_file)
        self.assertEqual(self.transactions_file.read_text(encoding="utf-8"), "{not json")


class ListenerTests(StateTestCase):
    def test_every_change_notifies_the_screens(self):
        calls = []
        self.state.subscribe(lambda: calls.append("refresh"))
        self.add("expense", "5", "Food", "Tea", "2026-11-12")
        self.state.edit_transaction("T0001", amount="6")
        self.state.delete_transaction("T0001")
        self.state.create_budget("Food", "2026-11", "50")
        self.assertEqual(len(calls), 4)

    def test_a_rejected_change_does_not_notify(self):
        calls = []
        self.state.subscribe(lambda: calls.append("refresh"))
        with self.assertRaises(ValidationError):
            self.add("expense", "abc", "Food", "Tea", "2026-11-12")
        self.assertEqual(calls, [])

    def test_screens_are_still_refreshed_when_saving_fails(self):
        calls = []
        self.state.subscribe(lambda: calls.append("refresh"))
        with mock.patch("gui.app_state.save_transactions", side_effect=StorageError("disk full")):
            with self.assertRaises(StorageError):
                self.add("expense", "5", "Food", "Tea", "2026-11-12")
        self.assertEqual(calls, ["refresh"])        # the change is in memory, so screens must show it
        self.assertEqual(len(self.state.transactions), 1)


class InformationTests(StateTestCase):
    def setUp(self):
        super().setUp()
        self.add("income", "2000", "Salary", "Pay", "2026-10-31")
        self.add("expense", "50", "Food", "October shop", "2026-10-20")
        self.add("expense", "40", "food", "November shop", "2026-11-02")
        self.add("expense", "30", "Bills", "Water", "2026-11-03")
        self.state.create_budget("Travel", "2026-12", "500")

    def test_all_time_and_one_month(self):
        self.assertEqual(len(self.state.period_transactions(None)), 4)
        self.assertEqual(len(self.state.period_transactions(ALL_TIME)), 4)
        self.assertEqual(len(self.state.period_transactions("2026-11")), 2)
        self.assertEqual(self.state.period_transactions("2030-01"), [])

    def test_categories_include_budgets_and_ignore_case_differences(self):
        self.assertEqual(self.state.categories(), ["Bills", "Food", "Salary", "Travel"])

    def test_months_include_budget_months_newest_first(self):
        self.assertEqual(self.state.months(), ["2026-12", "2026-11", "2026-10"])


class ExportTests(StateTestCase):
    def test_export_writes_every_transaction(self):
        self.add("income", "100", "Gift", "Present", "2026-11-12")
        self.add("expense", "10", "Food", "Tea", "2026-11-13")
        target = self.folder / "out.csv"
        self.assertEqual(self.state.export_csv(target), 2)
        self.assertEqual(len(target.read_text(encoding="utf-8-sig").strip().splitlines()), 3)

    def test_exporting_over_a_data_file_is_refused(self):
        self.add("income", "100", "Gift", "Present", "2026-11-12")
        before = self.transactions_file.read_text(encoding="utf-8")
        for protected in (self.transactions_file, self.budgets_file):
            with self.subTest(file=protected.name):
                with self.assertRaises(ValidationError):
                    self.state.export_csv(protected)
        self.assertEqual(self.transactions_file.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()