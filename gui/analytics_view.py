"""The Analytics tab: the full set of figures for all time or one month."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from finance_core.analytics_service import (
    expense_by_category,
    highest_expense_category,
    monthly_summaries,
    summarise,
    top_transactions,
)
from finance_core.display import format_money, format_percent
from gui import theme
from gui.app_state import AppState
from gui.widgets import Column, DataTable, PeriodSelector, shorten

TOP_COUNT = 5


class AnalyticsView(ttk.Frame):
    def __init__(self, parent: tk.Misc, app_state: AppState) -> None:
        super().__init__(parent, padding=12)
        self.app_state = app_state

        top = ttk.Frame(self)
        top.pack(fill="x")
        self.period = PeriodSelector(top, self.refresh)
        self.period.pack(side="left")

        grid = ttk.Frame(self)
        grid.pack(fill="both", expand=True, pady=(10, 0))
        for column in (0, 1):
            grid.columnconfigure(column, weight=1, uniform="half")
        for row in (0, 1):
            grid.rowconfigure(row, weight=1, uniform="rows")

        summary_box = ttk.LabelFrame(grid, text="Financial summary", padding=10)
        summary_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self.figures: dict[str, ttk.Label] = {}
        for row, name in enumerate(("Total income", "Total expenses", "Net savings", "Savings rate",
                                    "Average expense", "Transactions counted", "Highest spending category")):
            ttk.Label(summary_box, text=name, style="Muted.TLabel").grid(row=row, column=0, sticky="w")
            value = ttk.Label(summary_box, text="-", font=("TkDefaultFont", 10, "bold"))
            value.grid(row=row, column=1, sticky="e", padx=(20, 0), pady=1)
            self.figures[name] = value
        summary_box.columnconfigure(1, weight=1)

        category_box = ttk.LabelFrame(grid, text="Spending by category", padding=8)
        category_box.grid(row=0, column=1, sticky="nsew", pady=(0, 8))
        self.categories = DataTable(category_box, [
            Column("category", "Category", 160, stretch=True),
            Column("spent", "Spent", 110, anchor="e"),
        ], height=6)
        self.categories.pack(fill="both", expand=True)

        monthly_box = ttk.LabelFrame(grid, text="Month by month", padding=8)
        monthly_box.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self.monthly = DataTable(monthly_box, [
            Column("month", "Month", 80),
            Column("income", "Income", 100, anchor="e"),
            Column("expenses", "Expenses", 100, anchor="e"),
            Column("net", "Net", 100, anchor="e", stretch=True),
        ], height=6)
        self.monthly.pack(fill="both", expand=True)

        top_box = ttk.LabelFrame(grid, text=f"Largest {TOP_COUNT} transactions", padding=8)
        top_box.grid(row=1, column=1, sticky="nsew")
        self.top = DataTable(top_box, [
            Column("id", "ID", 60),
            Column("category", "Category", 100),
            Column("description", "Description", 140, stretch=True),
            Column("amount", "Amount", 90, anchor="e"),
        ], height=6)
        self.top.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self) -> None:
        self.period.set_months(self.app_state.months())
        transactions = self.app_state.period_transactions(self.period.month())

        summary = summarise(transactions)
        net = summary.net_savings
        highest = highest_expense_category(transactions)
        values = {
            "Total income": format_money(summary.total_income),
            "Total expenses": format_money(summary.total_expenses),
            "Net savings": format_money(net),
            "Savings rate": format_percent(summary.savings_rate, missing="N/A (no income)"),
            "Average expense": format_money(summary.average_expense),
            "Transactions counted": str(summary.transaction_count),
            "Highest spending category": (
                f"{highest[0]} ({format_money(highest[1])})" if highest else "None"),
        }
        for name, text in values.items():
            self.figures[name].configure(text=text)
        self.figures["Net savings"].configure(foreground=theme.INCOME if net >= 0 else theme.EXPENSE)

        self.categories.set_rows([
            (f"c{index}", (shorten(category, 30), format_money(total)), "")
            for index, (category, total) in enumerate(expense_by_category(transactions).items())
        ])
        self.monthly.set_rows([
            (m.month, (m.month, format_money(m.income), format_money(m.expenses), format_money(m.net)), "")
            for m in monthly_summaries(transactions)
        ])
        self.top.set_rows([
            (t.transaction_id,
             (t.transaction_id, shorten(t.category, 16), shorten(t.description, 30), format_money(t.amount)),
             "")
            for t in top_transactions(transactions, TOP_COUNT)
        ])