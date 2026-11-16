import unittest
from unittest import mock

from tests.gui_support import GuiTestCase

from finance_core.storage import load_transactions
from gui.app_state import AppState
from gui.transactions_view import TransactionsView


class TransactionsViewTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.add("income", "1500", "Salary", "November pay", "2026-11-01")
        self.add("expense", "12.50", "Food", "Lunch with team", "2026-11-05")
        self.add("expense", "60", "Transport", "Monthly bus pass", "2026-11-05")
        self.add("expense", "30", "Food", "Groceries", "2026-11-20")
        self.view = TransactionsView(self.root, self.state, self.prompts)
        self.state.subscribe(self.view.refresh)

    def ids(self):
        return [row[0] for row in self.view.table.all_values()]

    def set_filters(self, text="", kind="All", category="", start="", end=""):
        self.view.text_var.set(text)
        self.view.type_var.set(kind)
        self.view.category_var.set(category)
        self.view.start_var.set(start)
        self.view.end_var.set(end)
        self.view.refresh()


class ListingTests(TransactionsViewTestCase):
    def test_all_transactions_are_listed_newest_first_with_formatted_amounts(self):
        # T0002 and T0003 share a date; newest-first is the exact reverse of oldest-first
        self.assertEqual(self.ids(), ["T0004", "T0003", "T0002", "T0001"])
        self.assertEqual(self.view.table.row_values("T0001")[-1], "1,500.00")
        self.assertIn("Showing 4 of 4", self.view.summary.cget("text"))

    def test_empty_state_message(self):
        empty_state = AppState(self.folder / "x.json", self.folder / "y.json")
        view = TransactionsView(self.root, empty_state, self.prompts)
        self.assertEqual(view.table.row_count, 0)
        self.assertIn("No transactions yet", view.summary.cget("text"))

    def test_new_data_appears_without_reopening_the_tab(self):
        self.add("expense", "5", "Food", "Tea", "2026-11-21")
        self.assertIn("T0005", self.ids())


class FilterTests(TransactionsViewTestCase):
    def test_filter_by_category(self):
        self.set_filters(category="food")
        self.assertEqual(self.ids(), ["T0004", "T0002"])
        self.assertIn("Showing 2 of 4", self.view.summary.cget("text"))

    def test_filter_by_description_words_ignoring_case(self):
        self.set_filters(text="BUS")
        self.assertEqual(self.ids(), ["T0003"])

    def test_filter_by_type(self):
        self.set_filters(kind="income")
        self.assertEqual(self.ids(), ["T0001"])

    def test_filter_by_date_range(self):
        self.set_filters(start="2026-11-05", end="2026-11-20")
        self.assertEqual(sorted(self.ids()), ["T0002", "T0003", "T0004"])

    def test_filters_combine(self):
        self.set_filters(kind="expense", category="Food", start="2026-11-10")
        self.assertEqual(self.ids(), ["T0004"])

    def test_no_match_message(self):
        self.set_filters(text="zebra")
        self.assertEqual(self.ids(), [])
        self.assertIn("No transactions match", self.view.summary.cget("text"))

    def test_invalid_filter_shows_a_message_and_keeps_the_old_list(self):
        self.set_filters(start="yesterday")
        self.assertIn("not a valid date", self.view.filter_error.cget("text"))
        self.assertEqual(len(self.ids()), 4)

    def test_reversed_range_shows_a_message(self):
        self.set_filters(start="2026-12-01", end="2026-11-01")
        self.assertIn("cannot be before", self.view.filter_error.cget("text"))

    def test_clear_restores_everything(self):
        self.set_filters(text="bus", kind="expense")
        self.view.clear_filters()
        self.assertEqual(len(self.ids()), 4)
        self.assertEqual(self.view.filter_error.cget("text"), "")


class SortTests(TransactionsViewTestCase):
    def test_clicking_a_heading_sorts_ascending_then_toggles(self):
        self.view.sort_by("amount")
        self.assertEqual(self.ids(), ["T0002", "T0004", "T0003", "T0001"])
        self.view.sort_by("amount")
        self.assertEqual(self.ids(), ["T0001", "T0003", "T0004", "T0002"])

    def test_an_arrow_marks_the_sorted_column(self):
        self.view.sort_by("amount")
        self.assertIn("\u25b2", self.view.table.tree.heading("amount", "text"))
        self.assertNotIn("\u25b2", self.view.table.tree.heading("date", "text"))
        self.view.sort_by("amount")
        self.assertIn("\u25bc", self.view.table.tree.heading("amount", "text"))

    def test_sort_by_category(self):
        self.view.sort_by("category")
        self.assertEqual(self.ids(), ["T0002", "T0004", "T0001", "T0003"])

    def test_columns_that_cannot_be_sorted_are_ignored(self):
        before = self.ids()
        self.view.sort_by("description")
        self.assertEqual(self.ids(), before)

    def test_sorting_applies_to_filtered_results(self):
        self.set_filters(category="Food")
        self.view.sort_by("amount")
        self.assertEqual(self.ids(), ["T0002", "T0004"])


class ActionTests(TransactionsViewTestCase):
    def test_add_buttons_open_the_form_with_the_right_type(self):
        with mock.patch("gui.dialogs.ask_transaction") as ask:
            self.view.add("income")
            ask.assert_called_once_with(self.view, self.state, default_type="income")

    def test_edit_opens_the_form_for_the_selected_transaction(self):
        self.view.table.select("T0003")
        with mock.patch("gui.dialogs.ask_transaction") as ask:
            self.view.edit_selected()
        self.assertEqual(ask.call_args.args[2].transaction_id, "T0003")

    def test_edit_and_delete_without_a_selection_show_a_hint_and_change_nothing(self):
        with mock.patch("gui.dialogs.ask_transaction") as ask:
            self.view.edit_selected()
            ask.assert_not_called()
        self.assertIn("Select a transaction", self.view.message.cget("text"))
        self.view.delete_selected()
        self.assertEqual(len(self.state.transactions), 4)
        self.assertEqual(self.prompts.confirms, [])

    def test_delete_asks_first_and_removes_from_screen_and_disk(self):
        self.view.table.select("T0002")
        self.view.delete_selected()
        self.assertIn("T0002", self.prompts.confirms[0][1])
        self.assertNotIn("T0002", self.ids())
        self.assertEqual(len(load_transactions(self.transactions_file)), 3)
        self.assertIn("Deleted T0002", self.view.message.cget("text"))

    def test_declining_the_confirmation_keeps_the_transaction(self):
        self.prompts.confirm_answer = False
        self.view.table.select("T0002")
        self.view.delete_selected()
        self.assertEqual(len(self.state.transactions), 4)
        self.assertIn("T0002", self.ids())

    def test_deleting_something_already_gone_shows_an_error_box(self):
        self.view.table.select("T0002")
        self.state.delete_transaction("T0002")
        self.view.table.set_rows([("T0002", ("T0002", "", "", "", "", ""), "")])   # stale row still on screen
        self.view.table.select("T0002")
        self.view.delete_selected()
        self.assertEqual(len(self.prompts.errors), 1)
        self.assertEqual(self.prompts.errors[0][0], "Could not delete")
        self.assertIn("No transaction found", self.prompts.errors[0][1])


if __name__ == "__main__":
    unittest.main()