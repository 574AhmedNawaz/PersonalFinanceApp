import unittest
from datetime import date
from decimal import Decimal

from finance_core.errors import TransactionNotFoundError, ValidationError
from finance_core.models import Transaction
from finance_core.transaction_service import TransactionService


def add_sample_expense(service: TransactionService) -> Transaction:
    return service.add_transaction(
        "expense", "12.50", "food", "Lunch", "2026-11-12"
    )


class AddTransactionTests(unittest.TestCase):
    def setUp(self):
        self.service = TransactionService()

    def test_add_expense_stores_clean_values(self):
        transaction = add_sample_expense(self.service)
        self.assertEqual(transaction.transaction_id, "T0001")
        self.assertEqual(transaction.transaction_type, "expense")
        self.assertEqual(transaction.amount, Decimal("12.50"))
        self.assertEqual(transaction.category, "Food")
        self.assertEqual(transaction.description, "Lunch")
        self.assertEqual(transaction.transaction_date, date(2026, 11, 12))
        self.assertEqual(len(self.service), 1)

    def test_add_income(self):
        transaction = self.service.add_transaction(
            "income", "1500", "Salary", "November pay", "2026-11-01"
        )
        self.assertEqual(transaction.transaction_type, "income")
        self.assertEqual(transaction.amount, Decimal("1500.00"))

    def test_ids_are_unique_and_sequential(self):
        first = add_sample_expense(self.service)
        second = add_sample_expense(self.service)
        self.assertEqual([first.transaction_id, second.transaction_id], ["T0001", "T0002"])

    def test_invalid_input_is_rejected_and_nothing_is_stored(self):
        invalid_calls = [
            ("transfer", "10", "Food", "x", "2026-11-12"),   # bad type
            ("expense", "0", "Food", "x", "2026-11-12"),     # zero amount
            ("expense", "-4", "Food", "x", "2026-11-12"),    # negative amount
            ("expense", "abc", "Food", "x", "2026-11-12"),   # non-numeric amount
            ("expense", "10", "", "x", "2026-11-12"),        # missing category
            ("expense", "10", "Food", "  ", "2026-11-12"),   # empty description
            ("expense", "10", "Food", "x", "2026-02-30"),    # impossible date
        ]
        for arguments in invalid_calls:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValidationError):
                    self.service.add_transaction(*arguments)
        self.assertEqual(len(self.service), 0)

    def test_rejected_add_does_not_consume_an_id(self):
        with self.assertRaises(ValidationError):
            self.service.add_transaction("expense", "0", "Food", "x", "2026-11-12")
        transaction = add_sample_expense(self.service)
        self.assertEqual(transaction.transaction_id, "T0001")


class ReadTransactionTests(unittest.TestCase):
    def setUp(self):
        self.service = TransactionService()
        self.transaction = add_sample_expense(self.service)

    def test_get_by_id_ignores_case_and_spaces(self):
        self.assertEqual(self.service.get_transaction(" t0001 "), self.transaction)

    def test_get_missing_id_raises(self):
        with self.assertRaises(TransactionNotFoundError):
            self.service.get_transaction("T9999")

    def test_get_all_returns_a_copy(self):
        listing = self.service.get_all_transactions()
        listing.clear()
        self.assertEqual(len(self.service.get_all_transactions()), 1)


class EditTransactionTests(unittest.TestCase):
    def setUp(self):
        self.service = TransactionService()
        self.original = add_sample_expense(self.service)

    def test_edit_changes_only_supplied_fields(self):
        updated = self.service.edit_transaction("T0001", amount="20", category="dining")
        self.assertEqual(updated.amount, Decimal("20.00"))
        self.assertEqual(updated.category, "Dining")
        self.assertEqual(updated.description, self.original.description)
        self.assertEqual(updated.transaction_date, self.original.transaction_date)
        self.assertEqual(self.service.get_transaction("T0001"), updated)

    def test_edit_can_change_type_and_date(self):
        updated = self.service.edit_transaction(
            "T0001", transaction_type="income", transaction_date="2026-12-01"
        )
        self.assertEqual(updated.transaction_type, "income")
        self.assertEqual(updated.transaction_date, date(2026, 12, 1))

    def test_invalid_edit_changes_nothing(self):
        with self.assertRaises(ValidationError):
            self.service.edit_transaction("T0001", amount="20", description="  ")
        self.assertEqual(self.service.get_transaction("T0001"), self.original)

    def test_edit_missing_transaction_raises(self):
        with self.assertRaises(TransactionNotFoundError):
            self.service.edit_transaction("T0042", amount="5")


class DeleteTransactionTests(unittest.TestCase):
    def setUp(self):
        self.service = TransactionService()
        add_sample_expense(self.service)
        add_sample_expense(self.service)

    def test_delete_removes_only_that_transaction(self):
        removed = self.service.delete_transaction("T0001")
        self.assertEqual(removed.transaction_id, "T0001")
        remaining = [t.transaction_id for t in self.service.get_all_transactions()]
        self.assertEqual(remaining, ["T0002"])

    def test_delete_missing_transaction_raises(self):
        with self.assertRaises(TransactionNotFoundError):
            self.service.delete_transaction("T0099")
        self.assertEqual(len(self.service), 2)

    def test_deleted_id_is_not_reused_in_same_session(self):
        self.service.delete_transaction("T0002")
        new = add_sample_expense(self.service)
        self.assertEqual(new.transaction_id, "T0003")


class LoadedTransactionTests(unittest.TestCase):
    def make(self, transaction_id: str) -> Transaction:
        return Transaction(
            transaction_id, "expense", Decimal("5.00"), "Food", "Snack", date(2026, 11, 1)
        )

    def test_new_ids_continue_after_loaded_ids(self):
        service = TransactionService([self.make("T0001"), self.make("T0007")])
        new = add_sample_expense(service)
        self.assertEqual(new.transaction_id, "T0008")

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValidationError):
            TransactionService([self.make("T0001"), self.make("T0001")])


if __name__ == "__main__":
    unittest.main()