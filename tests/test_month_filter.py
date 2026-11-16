import unittest
from datetime import date
from decimal import Decimal

from finance_core.analytics_service import transactions_in_month
from finance_core.errors import ValidationError
from finance_core.models import Transaction


def make(transaction_id, day):
    return Transaction(
        transaction_id, "expense", Decimal("1.00"), "Food", "x", date.fromisoformat(day)
    )


SAMPLE = [
    make("T0001", "2026-10-31"),
    make("T0002", "2026-11-01"),
    make("T0003", "2026-11-15"),
    make("T0004", "2026-11-30"),
    make("T0005", "2026-12-01"),
]


def ids(transactions):
    return [t.transaction_id for t in transactions]


class MonthFilterTests(unittest.TestCase):
    def test_only_transactions_in_that_month_are_returned(self):
        self.assertEqual(ids(transactions_in_month(SAMPLE, "2026-11")), ["T0002", "T0003", "T0004"])

    def test_first_and_last_day_of_the_month_are_included_neighbours_are_not(self):
        result = ids(transactions_in_month(SAMPLE, "2026-11"))
        self.assertIn("T0002", result)       # 1 November
        self.assertIn("T0004", result)       # 30 November
        self.assertNotIn("T0001", result)    # 31 October
        self.assertNotIn("T0005", result)    # 1 December

    def test_month_with_no_transactions_gives_an_empty_list(self):
        self.assertEqual(transactions_in_month(SAMPLE, "2030-01"), [])

    def test_empty_input(self):
        self.assertEqual(transactions_in_month([], "2026-11"), [])

    def test_a_short_month_spelling_is_accepted(self):
        self.assertEqual(len(transactions_in_month(SAMPLE, "2026-12")), 1)
        self.assertEqual(len(transactions_in_month(SAMPLE, "2026-1")), 0)

    def test_invalid_month_raises(self):
        for value in ["2026-13", "november", ""]:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    transactions_in_month(SAMPLE, value)


if __name__ == "__main__":
    unittest.main()