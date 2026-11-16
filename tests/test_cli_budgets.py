import unittest
from decimal import Decimal

from cli.budget_commands import (
    budget_menu,
    create_budget,
    delete_budget,
    edit_budget,
    view_budgets,
)
from tests.cli_support import CliTestCase


class CreateBudgetScreenTests(CliTestCase):
    def test_creating_a_budget_saves_it_to_disk(self):
        context = self.make_context("food", "2026-11", "300")
        create_budget(context)

        saved = self.saved_budgets()
        self.assertEqual(len(saved), 1)
        self.assertEqual((saved[0].category, saved[0].month), ("Food", "2026-11"))
        self.assertEqual(saved[0].limit, Decimal("300.00"))
        self.assertIn("Budget created: Food, 2026-11, limit 300.00.", self.text)

    def test_bad_values_are_re_asked(self):
        context = self.make_context(
            "Food",
            "November", "2026-11",   # month: wrong format, then fine
            "0", "-20", "150",       # limit: zero, negative, then fine
        )
        create_budget(context)
        self.assertIn("not a valid month", self.text)
        self.assertIn("greater than zero", self.text)
        self.assertEqual(self.saved_budgets()[0].limit, Decimal("150.00"))

    def test_duplicate_budget_is_refused(self):
        create_budget(self.make_context("Food", "2026-11", "300"))
        context = self.make_context("food", "2026-11", "500")
        context.console.run_action(lambda: create_budget(context))
        self.assertIn("already exists", self.text)
        self.assertEqual(self.saved_budgets()[0].limit, Decimal("300.00"))


class ViewBudgetsScreenTests(CliTestCase):
    def setUp(self):
        super().setUp()
        context = self.make_context()
        context.budgets.create_budget("Food", "2026-11", "100")
        context.budgets.create_budget("Transport", "2026-11", "60")
        context.budgets.create_budget("Bills", "2026-11", "200")
        context.budgets.create_budget("Fun", "2026-11", "50")
        context.budgets.create_budget("Food", "2026-12", "100")
        context.save_budgets()
        txns = context.transactions
        txns.add_transaction("expense", "85", "Food", "Shopping", "2026-11-03")        # approaching
        txns.add_transaction("expense", "60", "Transport", "Pass", "2026-11-04")       # fully used
        txns.add_transaction("expense", "250", "Bills", "Rent", "2026-11-05")          # exceeded
        txns.add_transaction("income", "999", "Food", "Refund", "2026-11-06")          # ignored
        txns.add_transaction("expense", "500", "Food", "December", "2026-12-01")       # other month
        context.save_transactions()

    def test_all_four_states_are_displayed_for_one_month(self):
        view_budgets(self.make_context("2026-11"))
        for status in ("Approaching limit", "Fully used", "Exceeded", "Within budget"):
            self.assertIn(status, self.text)
        self.assertIn("85.00", self.text)       # Food spent (income and other months ignored)
        self.assertIn("-50.00", self.text)      # Bills remaining (exceeded)
        self.assertIn("125.00%", self.text)     # Bills used
        self.assertNotIn("2026-12", self.text)

    def test_blank_month_shows_every_budget(self):
        view_budgets(self.make_context(""))
        self.assertIn("2026-11", self.text)
        self.assertIn("2026-12", self.text)

    def test_legend_explains_the_rules(self):
        view_budgets(self.make_context(""))
        self.assertIn("Within budget: under 80% used.", self.text)

    def test_month_with_no_budgets(self):
        view_budgets(self.make_context("2030-01"))
        self.assertIn("No budgets found.", self.text)

    def test_invalid_month_is_re_asked(self):
        view_budgets(self.make_context("13-2026", "2026-11"))
        self.assertIn("not a valid month", self.text)
        self.assertIn("Approaching limit", self.text)


class EditAndDeleteBudgetScreenTests(CliTestCase):
    def setUp(self):
        super().setUp()
        seed = self.make_context()
        seed.budgets.create_budget("Food", "2026-11", "300")
        seed.save_budgets()

    def test_edit_changes_and_saves_the_limit(self):
        edit_budget(self.make_context("food", "2026-11", "450.50"))
        self.assertEqual(self.saved_budgets()[0].limit, Decimal("450.50"))
        self.assertIn("limit is now 450.50", self.text)

    def test_invalid_new_limit_is_re_asked(self):
        context = self.make_context("Food", "2026-11", "abc", "400")
        edit_budget(context)
        self.assertIn("not a valid amount", self.text)
        self.assertEqual(self.saved_budgets()[0].limit, Decimal("400.00"))

    def test_edit_of_a_missing_budget_is_an_error_message(self):
        context = self.make_context("Travel", "2026-11")
        context.console.run_action(lambda: edit_budget(context))
        self.assertIn("Error: No budget found for Travel in 2026-11.", self.text)

    def test_delete_with_confirmation(self):
        delete_budget(self.make_context("Food", "2026-11", "y"))
        self.assertEqual(self.saved_budgets(), [])
        self.assertIn("Budget deleted.", self.text)

    def test_declining_keeps_the_budget(self):
        delete_budget(self.make_context("Food", "2026-11", "n"))
        self.assertEqual(len(self.saved_budgets()), 1)
        self.assertIn("Nothing was deleted.", self.text)

    def test_delete_of_a_missing_budget_is_an_error_message(self):
        context = self.make_context("Travel", "2026-11")
        context.console.run_action(lambda: delete_budget(context))
        self.assertIn("No budget found", self.text)


class BudgetMenuTests(CliTestCase):
    def test_create_view_and_go_back(self):
        context = self.make_context(
            "1", "Food", "2026-11", "100",   # 1 = create
            "2", "",                          # 2 = view, all months
            "5",                              # 5 = back
        )
        budget_menu(context)
        self.assertIn("1. Create a budget", self.text)
        self.assertIn("5. Back", self.text)
        self.assertIn("Within budget", self.text)
        self.assertEqual(len(self.saved_budgets()), 1)


if __name__ == "__main__":
    unittest.main()