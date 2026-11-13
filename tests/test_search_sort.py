import unittest
from datetime import date
from decimal import Decimal

from finance_core.errors import ValidationError
from finance_core.models import Transaction
from finance_core.transaction_search import search_transactions, sort_transactions


def make(transaction_id, kind, amount, category, description, day):
    return Transaction(
        transaction_id, kind, Decimal(amount), category, description, date.fromisoformat(day)
    )


SAMPLE = [
    make("T0001", "income", "1500.00", "Salary", "November pay", "2026-11-01"),
    make("T0002", "expense", "12.50", "Food", "Lunch with team", "2026-11-05"),
    make("T0003", "expense", "60.00", "Transport", "Monthly bus pass", "2026-11-05"),
    make("T0004", "expense", "30.00", "Food", "Groceries", "2026-11-20"),
    make("T0005", "expense", "45.00", "Bills", "Phone bill", "2026-12-01"),
]


def ids(transactions):
    return [t.transaction_id for t in transactions]


class SearchTests(unittest.TestCase):
    def test_no_criteria_returns_everything(self):
        self.assertEqual(ids(search_transactions(SAMPLE)), ids(SAMPLE))

    def test_blank_criteria_are_ignored(self):
        result = search_transactions(SAMPLE, transaction_id="", text="  ", category=None, on_date="")
        self.assertEqual(len(result), 5)

    def test_search_by_id_is_case_insensitive(self):
        self.assertEqual(ids(search_transactions(SAMPLE, transaction_id=" t0003 ")), ["T0003"])

    def test_search_by_description_substring_ignores_case(self):
        self.assertEqual(ids(search_transactions(SAMPLE, text="BILL")), ["T0005"])
        # 'o' appears in 4 of the 5 descriptions (not in "Lunch with team")
        self.assertEqual(
            ids(search_transactions(SAMPLE, text="o")), ["T0001", "T0003", "T0004", "T0005"]
        )

    def test_description_search_finds_partial_words(self):
        self.assertEqual(ids(search_transactions(SAMPLE, text="pass")), ["T0003"])

    def test_filter_by_type(self):
        self.assertEqual(ids(search_transactions(SAMPLE, transaction_type="income")), ["T0001"])
        self.assertEqual(len(search_transactions(SAMPLE, transaction_type="Expense")), 4)

    def test_filter_by_category_ignores_case(self):
        self.assertEqual(ids(search_transactions(SAMPLE, category="food")), ["T0002", "T0004"])

    def test_filter_by_single_date(self):
        self.assertEqual(ids(search_transactions(SAMPLE, on_date="2026-11-05")), ["T0002", "T0003"])

    def test_filter_by_date_range_is_inclusive(self):
        result = search_transactions(SAMPLE, start_date="2026-11-05", end_date="2026-11-20")
        self.assertEqual(ids(result), ["T0002", "T0003", "T0004"])

    def test_open_ended_ranges(self):
        self.assertEqual(ids(search_transactions(SAMPLE, start_date="2026-11-20")), ["T0004", "T0005"])
        self.assertEqual(ids(search_transactions(SAMPLE, end_date="2026-11-01")), ["T0001"])

    def test_filters_combine_with_and(self):
        result = search_transactions(
            SAMPLE, transaction_type="expense", category="Food", start_date="2026-11-10"
        )
        self.assertEqual(ids(result), ["T0004"])

    def test_no_match_returns_empty_list(self):
        self.assertEqual(search_transactions(SAMPLE, text="nothing like this"), [])
        self.assertEqual(search_transactions(SAMPLE, transaction_id="T9999"), [])

    def test_searching_an_empty_collection(self):
        self.assertEqual(search_transactions([], text="a"), [])

    def test_invalid_criteria_raise_validation_error(self):
        bad_searches = [
            {"transaction_type": "transfer"},
            {"on_date": "2026-02-30"},
            {"start_date": "yesterday"},
            {"start_date": "2026-12-01", "end_date": "2026-11-01"},   # reversed range
            {"on_date": "2026-11-05", "start_date": "2026-11-01"},    # date AND range
        ]
        for criteria in bad_searches:
            with self.subTest(criteria=criteria):
                with self.assertRaises(ValidationError):
                    search_transactions(SAMPLE, **criteria)

    def test_single_day_range_works(self):
        result = search_transactions(SAMPLE, start_date="2026-11-05", end_date="2026-11-05")
        self.assertEqual(ids(result), ["T0002", "T0003"])

    def test_search_does_not_change_the_input(self):
        original = list(SAMPLE)
        search_transactions(SAMPLE, category="Food")
        self.assertEqual(SAMPLE, original)


class SortTests(unittest.TestCase):
    def test_sort_by_date_ascending_and_descending(self):
        self.assertEqual(
            ids(sort_transactions(SAMPLE, "date")), ["T0001", "T0002", "T0003", "T0004", "T0005"]
        )
        self.assertEqual(
            ids(sort_transactions(SAMPLE, "date", descending=True)),
            ["T0005", "T0004", "T0003", "T0002", "T0001"],
        )

    def test_sort_by_amount(self):
        self.assertEqual(
            ids(sort_transactions(SAMPLE, "amount")), ["T0002", "T0004", "T0005", "T0003", "T0001"]
        )
        self.assertEqual(ids(sort_transactions(SAMPLE, "amount", descending=True))[0], "T0001")

    def test_sort_by_category_ignores_case_and_ties_use_id(self):
        result = sort_transactions(SAMPLE, "category")
        self.assertEqual(ids(result), ["T0005", "T0002", "T0004", "T0001", "T0003"])

    def test_sort_by_type(self):
        result = sort_transactions(SAMPLE, "type")
        self.assertEqual(result[0].transaction_type, "expense")
        self.assertEqual(result[-1].transaction_type, "income")

    def test_equal_dates_keep_a_predictable_order(self):
        result = sort_transactions(SAMPLE, "date")
        self.assertEqual(ids(result)[1:3], ["T0002", "T0003"])

    def test_sort_option_is_case_insensitive(self):
        self.assertEqual(ids(sort_transactions(SAMPLE, " Amount ")), ids(sort_transactions(SAMPLE, "amount")))

    def test_unknown_sort_field_raises(self):
        with self.assertRaises(ValidationError):
            sort_transactions(SAMPLE, "colour")

    def test_sorting_empty_and_single_item_lists(self):
        self.assertEqual(sort_transactions([], "date"), [])
        self.assertEqual(sort_transactions(SAMPLE[:1], "amount"), SAMPLE[:1])

    def test_sort_does_not_change_the_input(self):
        original = list(SAMPLE)
        sort_transactions(SAMPLE, "amount", descending=True)
        self.assertEqual(SAMPLE, original)

    def test_search_then_sort(self):
        food = search_transactions(SAMPLE, category="Food")
        self.assertEqual(ids(sort_transactions(food, "amount", descending=True)), ["T0004", "T0002"])


if __name__ == "__main__":
    unittest.main()