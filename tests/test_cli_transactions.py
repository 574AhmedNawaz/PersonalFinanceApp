import unittest
from datetime import date
from decimal import Decimal

from cli.transaction_commands import (
    add_transaction,
    delete_transaction,
    edit_transaction,
    transaction_menu,
    view_transactions,
)
from tests.cli_support import CliTestCase


class AddTransactionScreenTests(CliTestCase):
    def test_adding_an_expense_saves_it_to_disk(self):
        context = self.make_context("12.50", "food", "Lunch", "2026-11-12")
        add_transaction(context, "expense")

        saved = self.saved_transactions()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].transaction_type, "expense")
        self.assertEqual(saved[0].amount, Decimal("12.50"))
        self.assertEqual(saved[0].category, "Food")
        self.assertIn("Added expense T0001: 12.50", self.text)

    def test_adding_income(self):
        context = self.make_context("1500", "Salary", "November pay", "2026-11-01")
        add_transaction(context, "income")
        self.assertEqual(self.saved_transactions()[0].transaction_type, "income")

    def test_bad_answers_are_re_asked_with_a_helpful_message(self):
        context = self.make_context(
            "abc", "-5", "10",          # amount: not a number, negative, then fine
            "Food",
            "", "Snack",               # description: empty, then fine
            "31/12/2026", "2026-12-31",  # date: wrong format, then fine
        )
        add_transaction(context, "expense")

        self.assertIn("not a valid amount", self.text)
        self.assertIn("greater than zero", self.text)
        self.assertIn("Description cannot be empty", self.text)
        self.assertIn("not a valid date", self.text)
        saved = self.saved_transactions()[0]
        self.assertEqual((saved.amount, saved.description), (Decimal("10.00"), "Snack"))
        self.assertEqual(saved.transaction_date, date(2026, 12, 31))

    def test_blank_date_means_today(self):
        context = self.make_context("5", "Food", "Tea", "")
        add_transaction(context, "expense")
        self.assertEqual(self.saved_transactions()[0].transaction_date, date.today())

    def test_cancel_stops_without_saving(self):
        context = self.make_context("5", "cancel")
        context.console.run_action(lambda: add_transaction(context, "expense"))
        self.assertIn("Cancelled.", self.text)
        self.assertEqual(self.saved_transactions(), [])


class ViewTransactionsScreenTests(CliTestCase):
    def test_empty_message(self):
        view_transactions(self.make_context())
        self.assertIn("No transactions recorded yet.", self.text)

    def test_lists_every_transaction_with_a_count(self):
        context = self.make_context()
        context.transactions.add_transaction("income", "1500", "Salary", "Pay", "2026-11-01")
        context.transactions.add_transaction("expense", "1234.5", "Food", "Big shop", "2026-11-02")
        view_transactions(context)
        self.assertIn("Pay", self.text)
        self.assertIn("1,500.00", self.text)
        self.assertIn("1,234.50", self.text)
        self.assertIn("2 transaction(s).", self.text)


class EditTransactionScreenTests(CliTestCase):
    def setUp(self):
        super().setUp()
        seed = self.make_context("12.50", "Food", "Lunch", "2026-11-12")
        add_transaction(seed, "expense")
        self.lines.clear()

    def test_only_the_changed_fields_are_updated_and_saved(self):
        context = self.make_context("t0001", "", "20", "", "", "")
        edit_transaction(context)

        saved = self.saved_transactions()[0]
        self.assertEqual(saved.amount, Decimal("20.00"))
        self.assertEqual(saved.category, "Food")
        self.assertEqual(saved.description, "Lunch")
        self.assertIn("Updated:", self.text)

    def test_pressing_enter_everywhere_changes_nothing(self):
        context = self.make_context("T0001", "", "", "", "", "")
        edit_transaction(context)
        self.assertIn("Nothing was changed.", self.text)
        self.assertEqual(self.saved_transactions()[0].amount, Decimal("12.50"))

    def test_invalid_new_value_is_re_asked(self):
        context = self.make_context("T0001", "", "oops", "30", "", "", "")
        edit_transaction(context)
        self.assertIn("not a valid amount", self.text)
        self.assertEqual(self.saved_transactions()[0].amount, Decimal("30.00"))

    def test_unknown_id_gives_a_clear_error(self):
        context = self.make_context("T9999")
        context.console.run_action(lambda: edit_transaction(context))
        self.assertIn("Error: No transaction found with ID 'T9999'.", self.text)


class DeleteTransactionScreenTests(CliTestCase):
    def setUp(self):
        super().setUp()
        seed = self.make_context("12.50", "Food", "Lunch", "2026-11-12")
        add_transaction(seed, "expense")
        self.lines.clear()

    def test_confirming_deletes_and_saves(self):
        context = self.make_context("T0001", "y")
        delete_transaction(context)
        self.assertEqual(self.saved_transactions(), [])
        self.assertIn("Deleted T0001.", self.text)

    def test_declining_keeps_the_transaction(self):
        context = self.make_context("T0001", "n")
        delete_transaction(context)
        self.assertEqual(len(self.saved_transactions()), 1)
        self.assertIn("Nothing was deleted.", self.text)

    def test_unknown_id_deletes_nothing(self):
        context = self.make_context("T0042")
        context.console.run_action(lambda: delete_transaction(context))
        self.assertIn("No transaction found", self.text)
        self.assertEqual(len(self.saved_transactions()), 1)


class TransactionMenuTests(CliTestCase):
    def test_menu_navigation_add_view_and_back(self):
        context = self.make_context(
            "2", "20", "Food", "Dinner", "2026-11-12",   # 2 = add expense
            "3",                                          # 3 = view all
            "6",                                          # 6 = back
        )
        transaction_menu(context)
        self.assertIn("1. Add income", self.text)
        self.assertIn("6. Back", self.text)
        self.assertIn("Dinner", self.text)
        self.assertEqual(len(self.saved_transactions()), 1)

    def test_an_error_inside_the_menu_does_not_end_the_session(self):
        context = self.make_context("5", "T9999", "6")   # delete unknown ID, then back
        transaction_menu(context)
        self.assertIn("Error: No transaction found", self.text)


class PersistenceAcrossSessionsTests(CliTestCase):
    def test_data_added_in_one_session_is_there_in_the_next(self):
        first = self.make_context("9.99", "Food", "Coffee beans", "2026-11-12")
        add_transaction(first, "expense")

        second = self.make_context()          # a fresh context reads the file again
        view_transactions(second)
        self.assertIn("Coffee beans", self.text)
        self.assertIn("9.99", self.text)


if __name__ == "__main__":
    unittest.main()