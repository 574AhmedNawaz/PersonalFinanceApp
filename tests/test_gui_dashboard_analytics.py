import unittest

from tests.gui_support import GuiTestCase

from cli.analytics_commands import show_analytics
from cli.console import Console
from cli.context import AppContext
from gui import theme
from gui.analytics_view import AnalyticsView
from gui.dashboard_view import DashboardView


class SeededTestCase(GuiTestCase):
    def setUp(self):
        super().setUp()
        # income 2500, expenses 500, net 2000, savings rate 80%, average 125
        self.add("income", "2000", "Salary", "Pay", "2026-10-31")
        self.add("income", "500", "Freelance", "Gig", "2026-11-15")
        self.add("expense", "100", "Food", "October food", "2026-10-20")
        self.add("expense", "50.50", "Food", "November food", "2026-11-02")
        self.add("expense", "49.50", "Transport", "Bus", "2026-11-03")
        self.add("expense", "300", "Bills", "Rent", "2026-11-04")


class DashboardTests(SeededTestCase):
    def setUp(self):
        super().setUp()
        self.view = DashboardView(self.root, self.state)
        self.state.subscribe(self.view.refresh)

    def test_headline_cards_for_all_time(self):
        self.assertEqual(self.view.income_card.text, "2,500.00")
        self.assertEqual(self.view.expense_card.text, "500.00")
        self.assertEqual(self.view.net_card.text, "2,000.00")
        self.assertEqual(self.view.rate_card.text, "80.00%")

    def test_cards_follow_the_chosen_month(self):
        self.view.period.choose("2026-11")
        self.assertEqual(self.view.income_card.text, "500.00")
        self.assertEqual(self.view.expense_card.text, "400.00")
        self.assertEqual(self.view.net_card.text, "100.00")
        self.assertEqual(self.view.rate_card.text, "20.00%")

    def test_chart_lists_categories_largest_first(self):
        self.assertEqual(self.view.chart.item_count, 3)
        texts = [self.view.chart.itemcget(i, "text") for i in self.view.chart.find_all()
                 if self.view.chart.type(i) == "text"]
        self.assertEqual(texts[0], "Bills")
        self.assertIn("300.00", texts)

    def test_no_income_shows_not_applicable_and_a_negative_net(self):
        for transaction_id in ("T0001", "T0002"):
            self.state.delete_transaction(transaction_id)
        self.assertEqual(self.view.rate_card.text, "N/A (no income)")
        self.assertEqual(self.view.net_card.text, "-500.00")

    def test_empty_data_does_not_fail(self):
        for transaction in self.state.transactions.get_all_transactions():
            self.state.delete_transaction(transaction.transaction_id)
        self.assertEqual(self.view.income_card.text, "0.00")
        self.assertEqual(self.view.chart.item_count, 0)
        self.assertEqual(self.view.recent.row_count, 0)

    def test_recent_transactions_are_the_newest_five_first(self):
        dates = [row[0] for row in self.view.recent.all_values()]
        self.assertEqual(len(dates), 5)
        self.assertEqual(dates, sorted(dates, reverse=True))
        self.assertNotIn("2026-10-20", dates)           # the oldest one is left out

    def test_only_budgets_needing_attention_are_listed(self):
        self.state.create_budget("Food", "2026-11", "1000")        # 5% used: fine, not listed
        self.state.create_budget("Bills", "2026-11", "300")        # exactly used
        self.state.create_budget("Transport", "2026-11", "55")     # 90%: approaching
        self.state.create_budget("Fun", "2026-11", "10")           # nothing spent: within budget
        statuses = {row[0]: row[3] for row in self.view.alerts.all_values()}
        self.assertEqual(statuses, {"Bills": "Fully used", "Transport": "Approaching limit"})

    def test_message_when_nothing_needs_attention(self):
        self.assertIn("No budgets are close", self.view.alert_note.cget("text"))

    def test_net_savings_is_green_when_positive_and_red_when_negative(self):
        self.assertEqual(str(self.view.net_card._value.cget("foreground")), theme.INCOME)
        self.view.period.choose("2026-10")                  # income 2000, expenses 100
        self.assertEqual(str(self.view.net_card._value.cget("foreground")), theme.INCOME)
        self.state.add_transaction(transaction_type="expense", amount="5000", category="Car",
                                   description="New car", transaction_date="2026-10-25")
        self.assertEqual(str(self.view.net_card._value.cget("foreground")), theme.EXPENSE)


class AnalyticsTests(SeededTestCase):
    def setUp(self):
        super().setUp()
        self.view = AnalyticsView(self.root, self.state)
        self.state.subscribe(self.view.refresh)

    def figure(self, name):
        return self.view.figures[name].cget("text")

    def test_all_time_summary(self):
        self.assertEqual(self.figure("Total income"), "2,500.00")
        self.assertEqual(self.figure("Total expenses"), "500.00")
        self.assertEqual(self.figure("Net savings"), "2,000.00")
        self.assertEqual(self.figure("Savings rate"), "80.00%")
        self.assertEqual(self.figure("Average expense"), "125.00")
        self.assertEqual(self.figure("Transactions counted"), "6")
        self.assertEqual(self.figure("Highest spending category"), "Bills (300.00)")

    def test_a_single_month_uses_only_that_months_transactions(self):
        self.view.period.choose("2026-11")
        self.assertEqual(self.figure("Total income"), "500.00")
        self.assertEqual(self.figure("Total expenses"), "400.00")
        self.assertEqual(self.figure("Savings rate"), "20.00%")
        self.assertEqual(self.figure("Average expense"), "133.33")
        self.assertEqual(self.figure("Transactions counted"), "4")

    def test_category_table_is_largest_first(self):
        self.assertEqual(self.view.categories.all_values(),
                         [["Bills", "300.00"], ["Food", "150.50"], ["Transport", "49.50"]])

    def test_month_by_month_table(self):
        self.assertEqual(self.view.monthly.all_values(), [
            ["2026-10", "2,000.00", "100.00", "1,900.00"],
            ["2026-11", "500.00", "400.00", "100.00"],
        ])

    def test_largest_transactions_table(self):
        rows = self.view.top.all_values()
        self.assertEqual([row[0] for row in rows], ["T0001", "T0002", "T0006", "T0003", "T0004"])
        self.assertEqual(rows[0][3], "2,000.00")

    def test_zero_income_shows_not_applicable(self):
        for transaction_id in ("T0001", "T0002"):
            self.state.delete_transaction(transaction_id)
        self.assertEqual(self.figure("Savings rate"), "N/A (no income)")
        self.assertEqual(self.figure("Net savings"), "-500.00")

    def test_empty_data_does_not_fail(self):
        for transaction in self.state.transactions.get_all_transactions():
            self.state.delete_transaction(transaction.transaction_id)
        self.assertEqual(self.figure("Transactions counted"), "0")
        self.assertEqual(self.figure("Highest spending category"), "None")
        self.assertEqual(self.view.categories.row_count, 0)

    def test_the_same_figures_as_the_command_line_version(self):
        """The CLI and GUI call the same core functions, so their numbers must match."""
        lines = []
        console = Console(input_func=lambda prompt="": "", output_func=lines.append)
        context = AppContext(console, self.state.transactions, self.state.budgets,
                             self.transactions_file, self.budgets_file, self.folder / "export.csv")
        show_analytics(context)
        printed = "\n".join(lines)
        for name in ("Total income", "Total expenses", "Net savings", "Average expense"):
            self.assertIn(self.figure(name), printed)


if __name__ == "__main__":
    unittest.main()