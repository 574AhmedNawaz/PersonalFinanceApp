import unittest
from datetime import date
from decimal import Decimal

from tests.gui_support import GuiTestCase

from gui.dialogs import BudgetDialog, TransactionDialog


def fill(dialog, **values):
    for key, value in values.items():
        dialog.vars[key].set(value)


class AddTransactionDialogTests(GuiTestCase):
    def open(self, **kwargs):
        dialog = TransactionDialog(self.root, self.state, **kwargs)
        self.addCleanup(dialog.destroy)
        return dialog

    def test_form_starts_with_todays_date_and_the_chosen_type(self):
        dialog = self.open(default_type="income")
        self.assertEqual(dialog.vars["transaction_type"].get(), "income")
        self.assertEqual(dialog.vars["transaction_date"].get(), date.today().isoformat())
        self.assertEqual(dialog.title(), "Add income")

    def test_a_valid_form_saves_and_closes(self):
        dialog = self.open()
        fill(dialog, amount="12.50", category="food", description="Lunch", transaction_date="2026-11-12")
        self.assertTrue(dialog.submit())
        self.assertEqual(dialog.result.transaction_id, "T0001")
        saved = self.state.transactions.get_transaction("T0001")
        self.assertEqual((saved.amount, saved.category), (Decimal("12.50"), "Food"))
        self.assertFalse(dialog.winfo_exists())

    def test_problems_are_shown_beside_each_field_and_nothing_is_saved(self):
        dialog = self.open()
        fill(dialog, amount="abc", category="", description="", transaction_date="12/11/2026")
        self.assertFalse(dialog.submit())
        self.assertEqual(set(dialog.error_texts), {"amount", "category", "description", "transaction_date"})
        self.assertIn("not a valid amount", dialog.error_texts["amount"])
        self.assertEqual(len(self.state.transactions), 0)
        self.assertTrue(dialog.winfo_exists())          # the form stays open so the user can fix it

    def test_fixing_the_problems_clears_the_messages(self):
        dialog = self.open()
        fill(dialog, amount="abc", category="Food", description="Tea")
        dialog.submit()
        self.assertIn("amount", dialog.error_texts)
        fill(dialog, amount="3")
        self.assertTrue(dialog.submit())

    def test_category_choices_come_from_existing_data(self):
        self.add("expense", "5", "Food", "Tea", "2026-11-12")
        self.state.create_budget("Travel", "2026-11", "100")
        dialog = self.open()
        self.assertEqual(list(dialog.widgets["category"].cget("values")), ["Food", "Travel"])

    def test_cancel_closes_without_saving(self):
        dialog = self.open()
        fill(dialog, amount="5", category="Food", description="Tea")
        dialog.cancel_button.invoke()
        self.assertFalse(dialog.winfo_exists())
        self.assertIsNone(dialog.result)
        self.assertEqual(len(self.state.transactions), 0)


class EditTransactionDialogTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.original = self.add("expense", "12.50", "Food", "Lunch", "2026-11-12")

    def open(self):
        dialog = TransactionDialog(self.root, self.state, self.original)
        self.addCleanup(dialog.destroy)
        return dialog

    def test_form_is_filled_with_the_current_values(self):
        dialog = self.open()
        self.assertEqual(dialog.title(), "Edit transaction")
        self.assertEqual(
            {key: variable.get() for key, variable in dialog.vars.items()},
            {"transaction_type": "expense", "amount": "12.50", "category": "Food",
             "description": "Lunch", "transaction_date": "2026-11-12"},
        )

    def test_saving_changes_the_existing_transaction_not_a_new_one(self):
        dialog = self.open()
        fill(dialog, amount="20", description="Big lunch")
        self.assertTrue(dialog.submit())
        self.assertEqual(len(self.state.transactions), 1)
        changed = self.state.transactions.get_transaction("T0001")
        self.assertEqual((changed.amount, changed.description), (Decimal("20.00"), "Big lunch"))

    def test_a_transaction_that_no_longer_exists_gives_a_message_in_the_form(self):
        dialog = self.open()
        self.state.delete_transaction("T0001")            # removed while the form was open
        fill(dialog, amount="20")
        self.assertFalse(dialog.submit())
        self.assertIn("No transaction found", dialog.form_error.cget("text"))


class BudgetDialogTests(GuiTestCase):
    def open(self, budget=None):
        dialog = BudgetDialog(self.root, self.state, budget)
        self.addCleanup(dialog.destroy)
        return dialog

    def test_create_a_budget(self):
        dialog = self.open()
        fill(dialog, category="food", month="2026-11", limit="300")
        self.assertTrue(dialog.submit())
        self.assertEqual(self.state.budgets.get_budget("Food", "2026-11").limit, Decimal("300.00"))

    def test_month_starts_as_the_current_month(self):
        self.assertEqual(self.open().vars["month"].get(), date.today().strftime("%Y-%m"))

    def test_problems_are_shown_beside_each_field(self):
        dialog = self.open()
        fill(dialog, category="", month="November", limit="0")
        self.assertFalse(dialog.submit())
        self.assertEqual(set(dialog.error_texts), {"category", "month", "limit"})

    def test_a_duplicate_budget_gives_a_message_in_the_form(self):
        self.state.create_budget("Food", "2026-11", "300")
        dialog = self.open()
        fill(dialog, category="Food", month="2026-11", limit="500")
        self.assertFalse(dialog.submit())
        self.assertIn("already exists", dialog.form_error.cget("text"))
        self.assertEqual(self.state.budgets.get_budget("Food", "2026-11").limit, Decimal("300.00"))

    def test_editing_changes_only_the_limit_and_locks_category_and_month(self):
        budget = self.state.create_budget("Food", "2026-11", "300")
        dialog = self.open(budget)
        self.assertEqual(dialog.title(), "Edit budget limit")
        self.assertTrue(dialog.widgets["category"].instate(["disabled"]))
        self.assertTrue(dialog.widgets["month"].instate(["disabled"]))
        fill(dialog, limit="450.50")
        self.assertTrue(dialog.submit())
        self.assertEqual(len(self.state.budgets), 1)
        self.assertEqual(self.state.budgets.get_budget("Food", "2026-11").limit, Decimal("450.50"))


if __name__ == "__main__":
    unittest.main()