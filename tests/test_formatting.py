import unittest
from datetime import date
from decimal import Decimal

from cli.formatting import (
    format_money,
    format_percent,
    format_table,
    transactions_table,
)
from finance_core.models import Transaction


class MoneyAndPercentTests(unittest.TestCase):
    def test_money_has_thousands_separator_and_two_places(self):
        self.assertEqual(format_money(Decimal("1234.5")), "1,234.50")
        self.assertEqual(format_money(Decimal("0")), "0.00")
        self.assertEqual(format_money(Decimal("1000000")), "1,000,000.00")

    def test_negative_money_keeps_its_sign(self):
        self.assertEqual(format_money(Decimal("-50")), "-50.00")

    def test_percent(self):
        self.assertEqual(format_percent(Decimal("80")), "80.00%")
        self.assertEqual(format_percent(Decimal("-12.5")), "-12.50%")

    def test_missing_percent_uses_the_given_text(self):
        self.assertEqual(format_percent(None), "N/A")
        self.assertEqual(format_percent(None, missing="N/A (no income)"), "N/A (no income)")


class TableTests(unittest.TestCase):
    def test_columns_are_aligned_with_numbers_on_the_right(self):
        rows = [["Food", "5.00"], ["Transport", "120.00"]]
        table = format_table(("Name", "Amount"), rows, right_aligned=(1,))
        self.assertEqual(
            table.splitlines(),
            [
                "Name       Amount",
                "---------  ------",
                "Food         5.00",
                "Transport  120.00",
            ],
        )

    def test_empty_table_shows_only_the_header(self):
        self.assertEqual(
            format_table(("A", "B"), []).splitlines(),
            ["A  B", "-  -"],
        )

    def test_wide_cells_widen_the_column(self):
        table = format_table(("X",), [["longer than header"]])
        self.assertEqual(table.splitlines()[1], "-" * len("longer than header"))


class TransactionTableTests(unittest.TestCase):
    def make(self, description, category="Food"):
        return Transaction(
            "T0001", "expense", Decimal("12.50"), category, description, date(2026, 11, 12)
        )

    def test_row_contains_every_field(self):
        text = transactions_table([self.make("Lunch")])
        self.assertIn("T0001", text)
        self.assertIn("2026-11-12", text)
        self.assertIn("expense", text)
        self.assertIn("Lunch", text)
        self.assertIn("12.50", text)

    def test_long_descriptions_are_shortened(self):
        text = transactions_table([self.make("x" * 80)])
        self.assertNotIn("x" * 80, text)
        self.assertIn("...", text)

    def test_line_breaks_in_descriptions_do_not_break_the_table(self):
        text = transactions_table([self.make("line one\nline two")])
        self.assertEqual(len(text.splitlines()), 3)  # header, dashes, one row
        self.assertIn("line one line two", text)


if __name__ == "__main__":
    unittest.main()