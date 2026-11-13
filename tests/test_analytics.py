import unittest
from datetime import date
from decimal import Decimal

from finance_core.analytics_service import (
    average_expense,
    expense_by_category,
    expense_by_category_and_month,
    highest_expense_category,
    monthly_summaries,
    month_key,
    net_savings,
    savings_rate,
    summarise,
    top_transactions,
    total_expenses,
    total_income,
)
from finance_core.models import Transaction


def make(transaction_id, kind, amount, category, day, description="x"):
    return Transaction(
        transaction_id, kind, Decimal(amount), category, description, date.fromisoformat(day)
    )


# Hand-calculated expected values:
#   income   = 2000.00 + 500.00           = 2500.00
#   expenses = 100.00 + 50.50 + 49.50 + 300.00 = 500.00
#   net      = 2500 - 500                  = 2000.00
#   rate     = 2000 / 2500 * 100           = 80.00
#   average  = 500 / 4                     = 125.00
SAMPLE = [
    make("T0001", "income", "2000.00", "Salary", "2026-10-31"),
    make("T0002", "income", "500.00", "Freelance", "2026-11-15"),
    make("T0003", "expense", "100.00", "Food", "2026-10-20"),
    make("T0004", "expense", "50.50", "Food", "2026-11-02"),
    make("T0005", "expense", "49.50", "Transport", "2026-11-03"),
    make("T0006", "expense", "300.00", "Bills", "2026-11-04"),
]


class TotalsTests(unittest.TestCase):
    def test_totals_and_net(self):
        self.assertEqual(total_income(SAMPLE), Decimal("2500.00"))
        self.assertEqual(total_expenses(SAMPLE), Decimal("500.00"))
        self.assertEqual(net_savings(SAMPLE), Decimal("2000.00"))

    def test_savings_rate(self):
        self.assertEqual(savings_rate(SAMPLE), Decimal("80.00"))

    def test_average_expense(self):
        self.assertEqual(average_expense(SAMPLE), Decimal("125.00"))

    def test_savings_rate_with_zero_income_is_none(self):
        expenses_only = [t for t in SAMPLE if t.transaction_type == "expense"]
        self.assertIsNone(savings_rate(expenses_only))

    def test_savings_rate_can_be_negative_when_overspending(self):
        data = [
            make("T0001", "income", "100.00", "Salary", "2026-11-01"),
            make("T0002", "expense", "150.00", "Food", "2026-11-02"),
        ]
        self.assertEqual(savings_rate(data), Decimal("-50.00"))
        self.assertEqual(net_savings(data), Decimal("-50.00"))

    def test_empty_data_gives_zero_not_errors(self):
        self.assertEqual(total_income([]), Decimal("0.00"))
        self.assertEqual(total_expenses([]), Decimal("0.00"))
        self.assertEqual(net_savings([]), Decimal("0.00"))
        self.assertEqual(average_expense([]), Decimal("0.00"))
        self.assertIsNone(savings_rate([]))
        self.assertIsNone(highest_expense_category([]))
        self.assertEqual(expense_by_category([]), {})
        self.assertEqual(monthly_summaries([]), [])

    def test_income_only_has_zero_average_expense(self):
        self.assertEqual(average_expense(SAMPLE[:2]), Decimal("0.00"))

    def test_money_arithmetic_is_exact(self):
        data = [
            make("T0001", "expense", "0.10", "Food", "2026-11-01"),
            make("T0002", "expense", "0.20", "Food", "2026-11-01"),
        ]
        self.assertEqual(total_expenses(data), Decimal("0.30"))

    def test_average_is_rounded_to_two_places(self):
        data = [
            make("T0001", "expense", "10.00", "Food", "2026-11-01"),
            make("T0002", "expense", "10.00", "Food", "2026-11-01"),
            make("T0003", "expense", "10.01", "Food", "2026-11-01"),
        ]
        self.assertEqual(average_expense(data), Decimal("10.00"))  # 30.01 / 3 = 10.0033


class GroupingTests(unittest.TestCase):
    def test_expense_by_category_is_sorted_largest_first(self):
        result = expense_by_category(SAMPLE)
        self.assertEqual(
            list(result.items()),
            [("Bills", Decimal("300.00")), ("Food", Decimal("150.50")), ("Transport", Decimal("49.50"))],
        )

    def test_income_is_not_counted_as_category_spending(self):
        self.assertNotIn("Salary", expense_by_category(SAMPLE))

    def test_highest_expense_category(self):
        self.assertEqual(highest_expense_category(SAMPLE), ("Bills", Decimal("300.00")))

    def test_tied_categories_resolve_alphabetically(self):
        data = [
            make("T0001", "expense", "50.00", "Zoo", "2026-11-01"),
            make("T0002", "expense", "50.00", "Art", "2026-11-01"),
        ]
        self.assertEqual(highest_expense_category(data)[0], "Art")

    def test_expense_by_category_and_month(self):
        result = expense_by_category_and_month(SAMPLE)
        self.assertEqual(result[("Food", "2026-10")], Decimal("100.00"))
        self.assertEqual(result[("Food", "2026-11")], Decimal("50.50"))
        self.assertEqual(result[("Bills", "2026-11")], Decimal("300.00"))
        self.assertEqual(len(result), 4)

    def test_monthly_summaries(self):
        october, november = monthly_summaries(SAMPLE)
        self.assertEqual(october.month, "2026-10")
        self.assertEqual((october.income, october.expenses), (Decimal("2000.00"), Decimal("100.00")))
        self.assertEqual(october.net, Decimal("1900.00"))
        self.assertEqual(november.month, "2026-11")
        self.assertEqual((november.income, november.expenses), (Decimal("500.00"), Decimal("400.00")))
        self.assertEqual(november.net, Decimal("100.00"))

    def test_monthly_summaries_are_in_date_order_and_include_one_sided_months(self):
        data = [
            make("T0001", "expense", "10.00", "Food", "2027-01-05"),
            make("T0002", "income", "20.00", "Gift", "2026-12-25"),
        ]
        months = monthly_summaries(data)
        self.assertEqual([m.month for m in months], ["2026-12", "2027-01"])
        self.assertEqual(months[0].expenses, Decimal("0.00"))
        self.assertEqual(months[1].income, Decimal("0.00"))

    def test_month_key(self):
        self.assertEqual(month_key(date(2026, 1, 9)), "2026-01")
        self.assertEqual(month_key(date(2026, 12, 31)), "2026-12")


class TopTransactionsTests(unittest.TestCase):
    def test_top_transactions_largest_first(self):
        result = top_transactions(SAMPLE, count=3)
        self.assertEqual([t.transaction_id for t in result], ["T0001", "T0002", "T0006"])

    def test_top_expenses_only(self):
        result = top_transactions(SAMPLE, count=2, transaction_type="expense")
        self.assertEqual([t.transaction_id for t in result], ["T0006", "T0003"])

    def test_count_larger_than_data_returns_everything_available(self):
        self.assertEqual(len(top_transactions(SAMPLE, count=50)), 6)

    def test_zero_or_negative_count_returns_nothing(self):
        self.assertEqual(top_transactions(SAMPLE, count=0), [])
        self.assertEqual(top_transactions(SAMPLE, count=-1), [])


class SummaryTests(unittest.TestCase):
    def test_summarise_matches_individual_functions(self):
        summary = summarise(SAMPLE)
        self.assertEqual(summary.total_income, Decimal("2500.00"))
        self.assertEqual(summary.total_expenses, Decimal("500.00"))
        self.assertEqual(summary.net_savings, Decimal("2000.00"))
        self.assertEqual(summary.savings_rate, Decimal("80.00"))
        self.assertEqual(summary.average_expense, Decimal("125.00"))
        self.assertEqual(summary.transaction_count, 6)

    def test_summarise_works_with_a_generator(self):
        summary = summarise(t for t in SAMPLE)
        self.assertEqual(summary.net_savings, Decimal("2000.00"))


if __name__ == "__main__":
    unittest.main()