import unittest
from decimal import Decimal

from tests.gui_support import GuiTestCase

from gui import theme
from gui.widgets import BarChart, Column, DataTable, PeriodSelector, SummaryCard, shorten


class ShortenTests(unittest.TestCase):
    def test_short_text_is_unchanged_and_long_text_is_cut(self):
        self.assertEqual(shorten("Food", 10), "Food")
        self.assertEqual(shorten("x" * 30, 10), "xxxxxxx...")

    def test_line_breaks_become_spaces(self):
        self.assertEqual(shorten("a\nb", 10), "a b")


class SummaryCardTests(GuiTestCase):
    def test_card_shows_the_value_it_is_given(self):
        card = SummaryCard(self.root, "Total income")
        self.assertEqual(card.text, "-")
        card.set("1,234.50", theme.INCOME)
        self.assertEqual(card.text, "1,234.50")


class BarChartTests(GuiTestCase):
    def test_empty_chart_shows_a_message_and_no_bars(self):
        chart = BarChart(self.root, "Nothing here.")
        chart.set_data([])
        texts = [chart.itemcget(item, "text") for item in chart.find_all()
                 if chart.type(item) == "text"]
        self.assertEqual(texts, ["Nothing here."])
        self.assertEqual(chart.item_count, 0)

    def test_each_item_gets_a_bar_a_label_and_an_amount(self):
        chart = BarChart(self.root)
        chart.set_data([("Bills", Decimal("250")), ("Food", Decimal("125.50"))])
        rectangles = [i for i in chart.find_all() if chart.type(i) == "rectangle"]
        texts = [chart.itemcget(i, "text") for i in chart.find_all() if chart.type(i) == "text"]
        self.assertEqual(len(rectangles), 2)
        for expected in ("Bills", "Food", "250.00", "125.50"):
            self.assertIn(expected, texts)

    def test_bar_length_is_proportional_to_the_amount(self):
        chart = BarChart(self.root)
        chart.set_data([("Big", Decimal("200")), ("Small", Decimal("50"))])
        lengths = []
        for item in chart.find_all():
            if chart.type(item) == "rectangle":
                x1, _, x2, _ = chart.coords(item)
                lengths.append(x2 - x1)
        self.assertAlmostEqual(lengths[0] / lengths[1], 4, delta=0.1)


class DataTableTests(GuiTestCase):
    def make(self, **options):
        return DataTable(self.root, [Column("a", "A", 80), Column("b", "B", 80, anchor="e")], **options)

    def test_rows_can_be_set_replaced_and_read_back(self):
        table = self.make()
        table.set_rows([("r1", ("x", "1"), ""), ("r2", ("y", "2"), "")])
        self.assertEqual(table.all_values(), [["x", "1"], ["y", "2"]])
        table.set_rows([("r3", ("z", "3"), "")])
        self.assertEqual(table.all_values(), [["z", "3"]])
        self.assertEqual(table.row_count, 1)

    def test_selection(self):
        table = self.make()
        table.set_rows([("r1", ("x", "1"), ""), ("r2", ("y", "2"), "")])
        self.assertIsNone(table.selected_id())
        table.select("r2")
        self.assertEqual(table.selected_id(), "r2")

    def test_heading_click_reports_the_column_key(self):
        clicked = []
        table = self.make(on_heading_click=clicked.append)
        self.root.tk.call(table.tree.heading("b", "command"))     # what a click on the heading runs
        self.assertEqual(clicked, ["b"])


class PeriodSelectorTests(GuiTestCase):
    def test_choices_and_selection(self):
        changes = []
        selector = PeriodSelector(self.root, lambda: changes.append(selector.month()))
        selector.set_months(["2026-12", "2026-11"])
        self.assertEqual(list(selector.combo.cget("values")), ["All time", "2026-12", "2026-11"])
        self.assertIsNone(selector.month())
        selector.choose("2026-11")
        self.assertEqual(selector.month(), "2026-11")
        self.assertEqual(changes, ["2026-11"])

    def test_a_chosen_month_that_disappears_falls_back_to_all_time(self):
        selector = PeriodSelector(self.root, lambda: None)
        selector.set_months(["2026-11"])
        selector.choose("2026-11")
        selector.set_months(["2026-12"])
        self.assertIsNone(selector.month())

    def test_a_chosen_month_that_still_exists_is_kept(self):
        selector = PeriodSelector(self.root, lambda: None)
        selector.set_months(["2026-11"])
        selector.choose("2026-11")
        selector.set_months(["2026-12", "2026-11"])
        self.assertEqual(selector.month(), "2026-11")


class ThemeTests(GuiTestCase):
    def test_applying_the_theme_twice_is_harmless(self):
        theme.apply_theme(self.root)
        theme.apply_theme(self.root)

    def test_every_budget_state_has_colours(self):
        self.assertEqual(
            set(theme.STATUS_COLOURS),
            {"Within budget", "Approaching limit", "Fully used", "Exceeded"},
        )


if __name__ == "__main__":
    unittest.main()