import unittest
from datetime import date
from decimal import Decimal

from finance_core.budget_service import (
    APPROACHING_LIMIT,
    EXCEEDED,
    FULLY_USED,
    WITHIN_BUDGET,
    BudgetService,
    classify_spending,
)
from finance_core.errors import BudgetNotFoundError, ValidationError
from finance_core.models import Budget, Transaction
from finance_core.validation import validate_month


def expense(transaction_id, amount, category, day):
    return Transaction(
        transaction_id, "expense", Decimal(amount), category, "x", date.fromisoformat(day)
    )


def income(transaction_id, amount, category, day):
    return Transaction(
        transaction_id, "income", Decimal(amount), category, "x", date.fromisoformat(day)
    )


class ValidateMonthTests(unittest.TestCase):
    def test_accepts_and_normalises_months(self):
        self.assertEqual(validate_month("2026-11"), "2026-11")
        self.assertEqual(validate_month(" 2026-1 "), "2026-01")

    def test_rejects_bad_months(self):
        for value in ["", "2026", "2026-13", "2026-00", "11-2026", "2026-11-05", "november"]:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_month(value)


class BudgetCrudTests(unittest.TestCase):
    def setUp(self):
        self.service = BudgetService()

    def test_create_budget_cleans_input(self):
        budget = self.service.create_budget(" food ", "2026-11", "300")
        self.assertEqual(budget, Budget("Food", "2026-11", Decimal("300.00")))
        self.assertEqual(len(self.service), 1)

    def test_duplicate_budget_is_rejected(self):
        self.service.create_budget("Food", "2026-11", "300")
        with self.assertRaises(ValidationError):
            self.service.create_budget("FOOD", "2026-11", "500")
        self.assertEqual(self.service.get_budget("Food", "2026-11").limit, Decimal("300.00"))

    def test_same_category_in_different_months_is_allowed(self):
        self.service.create_budget("Food", "2026-11", "300")
        self.service.create_budget("Food", "2026-12", "350")
        self.assertEqual(len(self.service), 2)

    def test_invalid_budget_values_are_rejected(self):
        bad_calls = [
            ("Food", "2026-11", "0"),
            ("Food", "2026-11", "-50"),
            ("Food", "2026-11", "abc"),
            ("Food", "2026-11", ""),
            ("", "2026-11", "100"),
            ("Food", "2026-13", "100"),
        ]
        for arguments in bad_calls:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValidationError):
                    self.service.create_budget(*arguments)
        self.assertEqual(len(self.service), 0)

    def test_edit_budget_changes_the_limit(self):
        self.service.create_budget("Food", "2026-11", "300")
        updated = self.service.edit_budget("food", "2026-11", "450.50")
        self.assertEqual(updated.limit, Decimal("450.50"))
        self.assertEqual(self.service.get_budget("Food", "2026-11"), updated)

    def test_invalid_edit_changes_nothing(self):
        self.service.create_budget("Food", "2026-11", "300")
        with self.assertRaises(ValidationError):
            self.service.edit_budget("Food", "2026-11", "-1")
        self.assertEqual(self.service.get_budget("Food", "2026-11").limit, Decimal("300.00"))

    def test_edit_or_delete_or_get_missing_budget_raises(self):
        with self.assertRaises(BudgetNotFoundError):
            self.service.edit_budget("Food", "2026-11", "100")
        with self.assertRaises(BudgetNotFoundError):
            self.service.delete_budget("Food", "2026-11")
        with self.assertRaises(BudgetNotFoundError):
            self.service.get_budget("Food", "2026-11")

    def test_delete_budget(self):
        self.service.create_budget("Food", "2026-11", "300")
        self.service.create_budget("Bills", "2026-11", "500")
        removed = self.service.delete_budget("Food", "2026-11")
        self.assertEqual(removed.category, "Food")
        self.assertEqual([b.category for b in self.service.get_all_budgets()], ["Bills"])

    def test_get_all_budgets_is_sorted_and_can_filter_by_month(self):
        self.service.create_budget("Transport", "2026-12", "100")
        self.service.create_budget("Food", "2026-12", "200")
        self.service.create_budget("Bills", "2026-11", "300")
        everything = [(b.month, b.category) for b in self.service.get_all_budgets()]
        self.assertEqual(
            everything, [("2026-11", "Bills"), ("2026-12", "Food"), ("2026-12", "Transport")]
        )
        december = self.service.get_all_budgets("2026-12")
        self.assertEqual([b.category for b in december], ["Food", "Transport"])

    def test_duplicates_in_constructor_are_rejected(self):
        budget = Budget("Food", "2026-11", Decimal("100.00"))
        with self.assertRaises(ValidationError):
            BudgetService([budget, budget])


class StatusRuleTests(unittest.TestCase):
    """Boundary cases for the four budget states (limit = 100.00)."""

    limit = Decimal("100.00")

    def test_zero_spending_is_within_budget(self):
        self.assertEqual(classify_spending(Decimal("0.00"), self.limit), WITHIN_BUDGET)

    def test_just_below_eighty_percent_is_within_budget(self):
        self.assertEqual(classify_spending(Decimal("79.99"), self.limit), WITHIN_BUDGET)

    def test_exactly_eighty_percent_is_approaching(self):
        self.assertEqual(classify_spending(Decimal("80.00"), self.limit), APPROACHING_LIMIT)

    def test_just_below_limit_is_approaching(self):
        self.assertEqual(classify_spending(Decimal("99.99"), self.limit), APPROACHING_LIMIT)

    def test_exactly_the_limit_is_fully_used(self):
        self.assertEqual(classify_spending(Decimal("100.00"), self.limit), FULLY_USED)

    def test_one_penny_over_is_exceeded(self):
        self.assertEqual(classify_spending(Decimal("100.01"), self.limit), EXCEEDED)

    def test_status_uses_exact_amounts_not_rounded_percentages(self):
        big_limit = Decimal("1000000.00")
        spent = Decimal("999999.99")  # displays as 100.00% but is not fully used
        self.assertEqual(classify_spending(spent, big_limit), APPROACHING_LIMIT)


class BudgetComparisonTests(unittest.TestCase):
    def setUp(self):
        self.service = BudgetService()
        self.service.create_budget("Food", "2026-11", "100")
        self.service.create_budget("Transport", "2026-11", "60")
        self.service.create_budget("Bills", "2026-11", "200")
        self.service.create_budget("Fun", "2026-11", "50")
        self.transactions = [
            expense("T0001", "30.00", "Food", "2026-11-02"),
            expense("T0002", "52.50", "Food", "2026-11-20"),     # Food total 82.50
            expense("T0003", "60.00", "Transport", "2026-11-05"),  # exactly the limit
            expense("T0004", "250.00", "Bills", "2026-11-28"),   # over the limit
            expense("T0005", "900.00", "Food", "2026-10-30"),    # other month: ignored
            income("T0006", "999.00", "Food", "2026-11-10"),     # income: ignored
        ]

    def statuses_by_category(self):
        return {s.category: s for s in self.service.get_statuses(self.transactions, "2026-11")}

    def test_spent_remaining_and_percentage(self):
        food = self.statuses_by_category()["Food"]
        self.assertEqual(food.spent, Decimal("82.50"))
        self.assertEqual(food.remaining, Decimal("17.50"))
        self.assertEqual(food.utilisation_percent, Decimal("82.50"))
        self.assertEqual(food.limit, Decimal("100.00"))

    def test_all_four_states_are_reported(self):
        by_category = self.statuses_by_category()
        self.assertEqual(by_category["Food"].status, APPROACHING_LIMIT)
        self.assertEqual(by_category["Transport"].status, FULLY_USED)
        self.assertEqual(by_category["Bills"].status, EXCEEDED)
        self.assertEqual(by_category["Fun"].status, WITHIN_BUDGET)

    def test_exceeded_budget_has_negative_remaining(self):
        bills = self.statuses_by_category()["Bills"]
        self.assertEqual(bills.remaining, Decimal("-50.00"))
        self.assertEqual(bills.utilisation_percent, Decimal("125.00"))

    def test_category_with_no_spending_shows_zero(self):
        fun = self.statuses_by_category()["Fun"]
        self.assertEqual(fun.spent, Decimal("0.00"))
        self.assertEqual(fun.remaining, Decimal("50.00"))
        self.assertEqual(fun.utilisation_percent, Decimal("0.00"))

    def test_income_never_counts_towards_a_budget(self):
        # Food has 999.00 of income in November; the Food status must ignore it.
        self.assertEqual(self.statuses_by_category()["Food"].spent, Decimal("82.50"))

    def test_other_months_do_not_count(self):
        self.service.create_budget("Food", "2026-10", "1000")
        october = {
            s.category: s for s in self.service.get_statuses(self.transactions, "2026-10")
        }
        self.assertEqual(october["Food"].spent, Decimal("900.00"))

    def test_without_month_all_budgets_are_reported(self):
        self.service.create_budget("Food", "2026-10", "1000")
        self.assertEqual(len(self.service.get_statuses(self.transactions)), 5)

    def test_no_transactions_means_every_budget_is_within_budget(self):
        statuses = self.service.get_statuses([])
        self.assertEqual({s.status for s in statuses}, {WITHIN_BUDGET})

    def test_no_budgets_gives_empty_result(self):
        self.assertEqual(BudgetService().get_statuses(self.transactions), [])


if __name__ == "__main__":
    unittest.main()