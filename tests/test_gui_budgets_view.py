import unittest
from decimal import Decimal
from unittest import mock

from tests.gui_support import GuiTestCase

from finance_core.storage import load_budgets
from gui.budgets_view import BudgetsView


class BudgetsViewTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        for category, month, limit in (("Food", "2026-11", "100"), ("Transport", "2026-11", "60"),
                                       ("Bills", "2026-11", "200"), ("Fun", "2026-11", "50"),
                                       ("Food", "2026-12", "100")):
            self.state.create_budget(category, month, limit)
        self.add("expense", "85", "Food", "Shop", "2026-11-03")          # 85%  approaching
        self.add("expense", "60", "Transport", "Pass", "2026-11-04")     # 100% fully used
        self.add("expense", "250", "Bills", "Rent", "2026-11-05")        # 125% exceeded
        self.add("income", "999", "Food", "Refund", "2026-11-06")        # income never counts
        self.add("expense", "500", "Food", "December", "2026-12-01")     # different month
        self.view = BudgetsView(self.root, self.state, self.prompts)
        self.state.subscribe(self.view.refresh)

    def rows_by_category(self, month=None):
        if month:
            self.view.period.choose(month)
        return {row[0] + " " + row[1]: row for row in self.view.table.all_values()}

    def test_all_four_states_are_shown_with_their_names(self):
        rows = self.rows_by_category("2026-11")
        self.assertEqual(rows["Food 2026-11"][6], "Approaching limit")
        self.assertEqual(rows["Transport 2026-11"][6], "Fully used")
        self.assertEqual(rows["Bills 2026-11"][6], "Exceeded")
        self.assertEqual(rows["Fun 2026-11"][6], "Within budget")

    def test_figures_use_expenses_of_that_month_only(self):
        food = self.rows_by_category("2026-11")["Food 2026-11"]
        self.assertEqual(food[2:6], ["100.00", "85.00", "15.00", "85.00%"])
        bills = self.rows_by_category()["Bills 2026-11"]
        self.assertEqual(bills[2:6], ["200.00", "250.00", "-50.00", "125.00%"])

    def test_each_state_has_its_own_row_colour(self):
        tree = self.view.table.tree
        colours = {str(tree.tag_configure(state, "background")) for state in
                   ("Within budget", "Approaching limit", "Fully used", "Exceeded")}
        self.assertEqual(len(colours), 4)

    def test_month_filter(self):
        self.view.period.choose("2026-12")
        self.assertEqual({row[1] for row in self.view.table.all_values()}, {"2026-12"})
        self.view.period.choose("All months")
        self.assertEqual(self.view.table.row_count, 5)

    def test_legend_explains_the_rules(self):
        text = self.view.legend.cget("text")
        for phrase in ("under 80%", "exactly 100%", "over 100%", "Only expenses count"):
            self.assertIn(phrase, text)

    def test_empty_message(self):
        for category, month in (("Food", "2026-11"), ("Transport", "2026-11"), ("Bills", "2026-11"),
                                ("Fun", "2026-11"), ("Food", "2026-12")):
            self.state.delete_budget(category, month)
        self.assertEqual(self.view.table.row_count, 0)
        self.assertIn("No budgets yet", self.view.empty_label.cget("text"))

    def select(self, category, month):
        for row_id in self.view.table.tree.get_children():
            values = self.view.table.row_values(row_id)
            if values[0] == category and values[1] == month:
                self.view.table.select(row_id)
                return
        self.fail("row not found")

    def test_add_opens_the_budget_form(self):
        with mock.patch("gui.dialogs.ask_budget") as ask:
            self.view.add()
            ask.assert_called_once_with(self.view, self.state)

    def test_edit_opens_the_form_for_the_selected_budget(self):
        self.select("Bills", "2026-11")
        with mock.patch("gui.dialogs.ask_budget") as ask:
            self.view.edit_selected()
        budget = ask.call_args.args[2]
        self.assertEqual((budget.category, budget.month, budget.limit),
                         ("Bills", "2026-11", Decimal("200.00")))

    def test_edit_and_delete_without_a_selection_show_a_hint(self):
        with mock.patch("gui.dialogs.ask_budget") as ask:
            self.view.edit_selected()
            ask.assert_not_called()
        self.view.delete_selected()
        self.assertIn("Select a budget", self.view.message.cget("text"))
        self.assertEqual(len(self.state.budgets), 5)

    def test_delete_asks_first_then_removes_the_budget_from_screen_and_disk(self):
        self.select("Fun", "2026-11")
        self.view.delete_selected()
        self.assertIn("Fun", self.prompts.confirms[0][1])
        self.assertEqual(len(load_budgets(self.budgets_file)), 4)
        self.assertNotIn("Fun 2026-11", self.rows_by_category())

    def test_declining_keeps_the_budget(self):
        self.prompts.confirm_answer = False
        self.select("Fun", "2026-11")
        self.view.delete_selected()
        self.assertEqual(len(self.state.budgets), 5)


if __name__ == "__main__":
    unittest.main()