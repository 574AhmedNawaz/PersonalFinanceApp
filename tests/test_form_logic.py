import unittest
from datetime import date
from decimal import Decimal

from gui.form_logic import ANY, check_budget_form, check_filter_form, check_transaction_form


class TransactionFormTests(unittest.TestCase):
    def check(self, **overrides):
        fields = dict(transaction_type="expense", amount="12.50", category="food",
                      description="Lunch", transaction_date="2026-11-12")
        fields.update(overrides)
        return check_transaction_form(**fields)

    def test_valid_form_gives_clean_values(self):
        result = self.check()
        self.assertTrue(result.ok)
        self.assertEqual(result.values["amount"], Decimal("12.50"))
        self.assertEqual(result.values["category"], "Food")
        self.assertEqual(result.values["transaction_date"], date(2026, 11, 12))

    def test_every_problem_is_reported_at_once_next_to_its_field(self):
        result = self.check(transaction_type="transfer", amount="abc", category="",
                            description="  ", transaction_date="12/11/2026")
        self.assertEqual(set(result.errors),
                         {"transaction_type", "amount", "category", "description", "transaction_date"})
        self.assertFalse(result.ok)

    def test_one_bad_field_does_not_hide_the_good_ones(self):
        result = self.check(amount="-5")
        self.assertEqual(list(result.errors), ["amount"])
        self.assertEqual(result.values["category"], "Food")

    def test_amount_rules_match_the_core_rules(self):
        for bad in ("0", "-1", "1.234", "abc", "", "nan", "9999999999"):
            with self.subTest(amount=bad):
                self.assertIn("amount", self.check(amount=bad).errors)
        for good in ("0.01", "7", "1000.50"):
            with self.subTest(amount=good):
                self.assertTrue(self.check(amount=good).ok)

    def test_blank_date_means_today(self):
        result = self.check(transaction_date="  ", today=date(2026, 1, 31))
        self.assertTrue(result.ok)
        self.assertEqual(result.values["transaction_date"], date(2026, 1, 31))

    def test_impossible_date_is_rejected(self):
        self.assertIn("transaction_date", self.check(transaction_date="2026-02-30").errors)


class BudgetFormTests(unittest.TestCase):
    def test_valid_budget(self):
        result = check_budget_form("food", "2026-11", "300")
        self.assertTrue(result.ok)
        self.assertEqual(result.values, {"category": "Food", "month": "2026-11", "limit": Decimal("300.00")})

    def test_every_problem_is_reported(self):
        result = check_budget_form("", "November", "0")
        self.assertEqual(set(result.errors), {"category", "month", "limit"})


class FilterFormTests(unittest.TestCase):
    def test_blank_filters_mean_no_filtering(self):
        result = check_filter_form("", ANY, "", "", "")
        self.assertTrue(result.ok)
        self.assertEqual(result.values, {
            "text": None, "transaction_type": None, "category": None,
            "start_date": None, "end_date": None,
        })

    def test_values_are_cleaned(self):
        result = check_filter_form("  bus ", "expense", "transport", "2026-11-01", "2026-11-30")
        self.assertTrue(result.ok)
        self.assertEqual(result.values["text"], "bus")
        self.assertEqual(result.values["category"], "Transport")
        self.assertEqual(result.values["start_date"], date(2026, 11, 1))

    def test_bad_date_is_reported_against_its_own_field(self):
        result = check_filter_form("", ANY, "", "yesterday", "")
        self.assertEqual(list(result.errors), ["start_date"])

    def test_reversed_range_is_reported(self):
        result = check_filter_form("", ANY, "", "2026-12-01", "2026-11-01")
        self.assertIn("end_date", result.errors)
        self.assertIn("cannot be before", result.errors["end_date"])

    def test_a_range_with_one_open_end_is_fine(self):
        self.assertTrue(check_filter_form("", ANY, "", "2026-11-01", "").ok)
        self.assertTrue(check_filter_form("", ANY, "", "", "2026-11-30").ok)


if __name__ == "__main__":
    unittest.main()