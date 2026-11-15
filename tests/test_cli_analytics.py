import unittest

from cli.analytics_commands import show_analytics
from tests.cli_support import CliTestCase


class AnalyticsScreenTests(CliTestCase):
    def seed(self, *rows):
        context = self.make_context()
        for row in rows:
            context.transactions.add_transaction(*row)
        context.save_transactions()

    def standard_data(self):
        # Same figures as the core analytics tests, worked out by hand:
        # income 2500, expenses 500, net 2000, savings rate 80%, average 125.
        self.seed(
            ("income", "2000", "Salary", "Pay", "2026-10-31"),
            ("income", "500", "Freelance", "Gig", "2026-11-15"),
            ("expense", "100", "Food", "October food", "2026-10-20"),
            ("expense", "50.50", "Food", "November food", "2026-11-02"),
            ("expense", "49.50", "Transport", "Bus", "2026-11-03"),
            ("expense", "300", "Bills", "Rent", "2026-11-04"),
        )

    def test_all_time_summary(self):
        self.standard_data()
        show_analytics(self.make_context(""))
        self.assertIn("FINANCIAL SUMMARY (all time)", self.text)
        self.assertIn("Total income:         2,500.00", self.text)
        self.assertIn("Total expenses:       500.00", self.text)
        self.assertIn("Net savings:          2,000.00", self.text)
        self.assertIn("Savings rate:         80.00%", self.text)
        self.assertIn("Average expense:      125.00", self.text)
        self.assertIn("Transactions counted: 6", self.text)

    def test_category_breakdown_and_highest_category(self):
        self.standard_data()
        show_analytics(self.make_context(""))
        self.assertIn("SPENDING BY CATEGORY", self.text)
        self.assertIn("Highest spending category: Bills (300.00)", self.text)
        # Bills (300) is listed before Food (150.50), which is before Transport (49.50)
        bills, food, transport = (self.text.find(name + " ") for name in ("Bills", "Food", "Transport"))
        self.assertTrue(0 < bills < food < transport)

    def test_month_by_month_section_lists_each_month(self):
        self.standard_data()
        show_analytics(self.make_context(""))
        self.assertIn("MONTH BY MONTH", self.text)
        self.assertIn("2026-10", self.text)
        self.assertIn("2026-11", self.text)

    def test_largest_transactions_section(self):
        self.standard_data()
        show_analytics(self.make_context(""))
        self.assertIn("LARGEST 5 TRANSACTIONS", self.text)
        top_section = self.text.split("LARGEST 5 TRANSACTIONS")[1]
        self.assertLess(top_section.find("Pay"), top_section.find("Rent"))   # 2000 before 300

    def test_a_single_month_uses_only_that_months_transactions(self):
        self.standard_data()
        show_analytics(self.make_context("2026-11"))
        # November: income 500, expenses 400, net 100, rate 20%, average 133.33
        self.assertIn("FINANCIAL SUMMARY (2026-11)", self.text)
        self.assertIn("Total income:         500.00", self.text)
        self.assertIn("Total expenses:       400.00", self.text)
        self.assertIn("Savings rate:         20.00%", self.text)
        self.assertIn("Average expense:      133.33", self.text)
        self.assertNotIn("October food", self.text)

    def test_zero_income_shows_not_applicable_instead_of_failing(self):
        self.seed(("expense", "40", "Food", "Shopping", "2026-11-02"))
        show_analytics(self.make_context(""))
        self.assertIn("Savings rate:         N/A (no income)", self.text)
        self.assertIn("Net savings:          -40.00", self.text)

    def test_income_only_has_no_expense_section_problems(self):
        self.seed(("income", "100", "Gift", "Present", "2026-11-02"))
        show_analytics(self.make_context(""))
        self.assertIn("No expenses in this period.", self.text)
        self.assertNotIn("Highest spending category", self.text)
        self.assertIn("Savings rate:         100.00%", self.text)

    def test_no_transactions_at_all(self):
        show_analytics(self.make_context(""))
        self.assertIn("No transactions for all time.", self.text)

    def test_month_with_no_transactions(self):
        self.standard_data()
        show_analytics(self.make_context("2030-01"))
        self.assertIn("No transactions for 2030-01.", self.text)

    def test_invalid_month_is_re_asked(self):
        self.standard_data()
        show_analytics(self.make_context("2026-99", "2026-11"))
        self.assertIn("not a valid month", self.text)
        self.assertIn("FINANCIAL SUMMARY (2026-11)", self.text)


if __name__ == "__main__":
    unittest.main()