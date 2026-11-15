import unittest

from cli.search_commands import run_search, run_sort
from tests.cli_support import CliTestCase


class SearchAndSortScreenTestCase(CliTestCase):
    """Starts each test with four saved transactions."""

    def setUp(self):
        super().setUp()
        context = self.make_context()
        service = context.transactions
        service.add_transaction("income", "1500", "Salary", "November pay", "2026-11-01")
        service.add_transaction("expense", "12.50", "Food", "Lunch with team", "2026-11-05")
        service.add_transaction("expense", "60", "Transport", "Monthly bus pass", "2026-11-05")
        service.add_transaction("expense", "30", "Food", "Groceries", "2026-11-20")
        context.save_transactions()

    def ids_in_output_order(self):
        """The transaction IDs in the order they appear in the printed output."""
        found = [(self.text.find(f"T000{n}"), f"T000{n}") for n in range(1, 5)]
        return [name for position, name in sorted(found) if position != -1]


class SearchScreenTests(SearchAndSortScreenTestCase):
    def test_filter_by_category(self):
        # id, text, type, category, exact date, from, to
        context = self.make_context("", "", "", "food", "", "", "")
        run_search(context)
        self.assertIn("2 transaction(s) found.", self.text)
        self.assertIn("Lunch with team", self.text)
        self.assertIn("Groceries", self.text)
        self.assertNotIn("Monthly bus pass", self.text)

    def test_search_by_description_words(self):
        context = self.make_context("", "BUS", "", "", "", "", "")
        run_search(context)
        self.assertIn("1 transaction(s) found.", self.text)
        self.assertIn("Monthly bus pass", self.text)

    def test_search_by_id(self):
        context = self.make_context("t0004", "", "", "", "", "", "")
        run_search(context)
        self.assertIn("Groceries", self.text)
        self.assertIn("1 transaction(s) found.", self.text)

    def test_exact_date_skips_the_range_questions(self):
        # With an exact date there are only five questions, not seven.
        context = self.make_context("", "", "", "", "2026-11-05")
        run_search(context)
        self.assertIn("2 transaction(s) found.", self.text)

    def test_date_range_and_type_combine(self):
        context = self.make_context("", "", "expense", "", "", "2026-11-10", "2026-11-30")
        run_search(context)
        self.assertIn("1 transaction(s) found.", self.text)
        self.assertIn("Groceries", self.text)

    def test_no_match_message(self):
        context = self.make_context("", "zebra", "", "", "", "", "")
        run_search(context)
        self.assertIn("No transactions match your search.", self.text)

    def test_invalid_type_is_re_asked(self):
        context = self.make_context("", "", "transfer", "income", "", "", "", "")
        run_search(context)
        self.assertIn("Transaction type must be", self.text)
        self.assertIn("1 transaction(s) found.", self.text)

    def test_reversed_date_range_shows_an_error_not_a_crash(self):
        context = self.make_context("", "", "", "", "", "2026-12-01", "2026-11-01")
        context.console.run_action(lambda: run_search(context))
        self.assertIn("Error: The start date cannot be after the end date.", self.text)

    def test_cancel_during_search(self):
        context = self.make_context("", "cancel")
        context.console.run_action(lambda: run_search(context))
        self.assertIn("Cancelled.", self.text)


class SortScreenTests(SearchAndSortScreenTestCase):
    def test_sort_by_amount_descending(self):
        run_sort(self.make_context("amount", "desc"))
        self.assertEqual(self.ids_in_output_order(), ["T0001", "T0003", "T0004", "T0002"])

    def test_sort_by_amount_ascending(self):
        run_sort(self.make_context("amount", "asc"))
        self.assertEqual(self.ids_in_output_order(), ["T0002", "T0004", "T0003", "T0001"])

    def test_sort_by_date_descending(self):
        run_sort(self.make_context("date", "desc"))
        # T0002 and T0003 share a date; descending is the exact reverse of ascending
        self.assertEqual(self.ids_in_output_order(), ["T0004", "T0003", "T0002", "T0001"])

    def test_sort_by_category(self):
        run_sort(self.make_context("category", "asc"))
        self.assertEqual(self.ids_in_output_order(), ["T0002", "T0004", "T0001", "T0003"])

    def test_invalid_field_is_re_asked(self):
        run_sort(self.make_context("colour", "amount", "asc"))
        self.assertIn("Please enter one of: date, amount, category, type", self.text)

    def test_sorting_with_no_transactions(self):
        self.transactions_file.unlink()
        run_sort(self.make_context())
        self.assertIn("No transactions recorded yet.", self.text)


if __name__ == "__main__":
    unittest.main()