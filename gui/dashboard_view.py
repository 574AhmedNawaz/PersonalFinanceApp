"""The Dashboard tab: headline figures, spending by category, budget alerts."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from finance_core.analytics_service import expense_by_category, summarise
from finance_core.budget_service import WITHIN_BUDGET
from finance_core.display import format_money, format_percent
from finance_core.transaction_search import sort_transactions
from gui import theme
from gui.app_state import AppState
from gui.widgets import BarChart, Column, DataTable, PeriodSelector, SummaryCard, shorten

RECENT_COUNT = 5
CHART_CATEGORIES = 6  # the biggest few categories keep the chart readable


class DashboardView(ttk.Frame):
    def __init__(self, parent: tk.Misc, app_state: AppState) -> None:
        super().__init__(parent, padding=12)
        self.app_state = app_state

        top = ttk.Frame(self)
        top.pack(fill="x")
        self.period = PeriodSelector(top, self.refresh)
        self.period.pack(side="left")

        cards = ttk.Frame(self)
        cards.pack(fill="x", pady=(10, 0))
        self.income_card = SummaryCard(cards, "Total income")
        self.expense_card = SummaryCard(cards, "Total expenses")
        self.net_card = SummaryCard(cards, "Net savings")
        self.rate_card = SummaryCard(cards, "Savings rate")
        for column, card in enumerate((self.income_card, self.expense_card, self.net_card, self.rate_card)):
            card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
            cards.columnconfigure(column, weight=1, uniform="cards")

        recent_box = ttk.LabelFrame(self, text="Most recent transactions", padding=8)
        recent_box.pack(side="bottom", fill="x", pady=(12, 0))

        middle = ttk.Frame(self)
        middle.pack(fill="both", expand=True, pady=(12, 0))
        middle.columnconfigure(0, weight=3, uniform="half")
        middle.columnconfigure(1, weight=2, uniform="half")

        chart_box = ttk.LabelFrame(middle, text="Spending by category", padding=8)
        chart_box.grid(row=0, column=0, sticky="nsew")
        self.chart = BarChart(chart_box, "No expenses in this period.")
        self.chart.pack(fill="both", expand=True)

        alert_box = ttk.LabelFrame(middle, text="Budget alerts", padding=8)
        alert_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.alerts = DataTable(alert_box, [
            Column("category", "Category", 90, stretch=True),
            Column("month", "Month", 70),
            Column("used", "Used", 75, anchor="e"),
            Column("status", "Status", 140),
        ], height=4)
        self.alerts.pack(fill="both", expand=True)
        for status, (background, foreground) in theme.STATUS_COLOURS.items():
            self.alerts.configure_tag(status, background=background, foreground=foreground)
        self.alert_note = ttk.Label(alert_box, text="", style="Muted.TLabel")
        self.alert_note.pack(anchor="w", pady=(4, 0))

        self.recent = DataTable(recent_box, [
            Column("date", "Date", 100),
            Column("type", "Type", 80),
            Column("category", "Category", 140),
            Column("description", "Description", 300, stretch=True),
            Column("amount", "Amount", 110, anchor="e"),
        ], height=RECENT_COUNT)
        self.recent.pack(fill="x")
        self.recent.configure_tag("income", foreground=theme.INCOME)
        self.recent.configure_tag("expense", foreground=theme.EXPENSE)
        self.refresh()

    def refresh(self) -> None:
        self.period.set_months(self.app_state.months())
        month = self.period.month()
        transactions = self.app_state.period_transactions(month)

        summary = summarise(transactions)
        self.income_card.set(format_money(summary.total_income), theme.INCOME)
        self.expense_card.set(format_money(summary.total_expenses), theme.EXPENSE)
        net = summary.net_savings
        self.net_card.set(format_money(net), theme.INCOME if net >= 0 else theme.EXPENSE)
        self.rate_card.set(format_percent(summary.savings_rate, missing="N/A (no income)"))

        totals = list(expense_by_category(transactions).items())
        self.chart.set_data(totals[:CHART_CATEGORIES])

        statuses = [
            s for s in self.app_state.budgets.get_statuses(
                self.app_state.transactions.get_all_transactions(), month)
            if s.status != WITHIN_BUDGET
        ]
        self.alerts.set_rows([
            (f"a{index}", (shorten(s.category, 18), s.month, format_percent(s.utilisation_percent), s.status),
             s.status)
            for index, s in enumerate(statuses)
        ])
        self.alert_note.configure(
            text="" if statuses else "No budgets are close to or over their limit.")

        newest = sort_transactions(transactions, "date", descending=True)[:RECENT_COUNT]
        self.recent.set_rows([
            (t.transaction_id,
             (t.transaction_date.isoformat(), t.transaction_type, t.category,
              shorten(t.description, 50), format_money(t.amount)),
             t.transaction_type)
            for t in newest
        ])