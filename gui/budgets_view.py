"""The Budgets tab: limits compared with what was actually spent."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from finance_core.budget_service import APPROACHING_PERCENT, BudgetStatus
from finance_core.display import format_money, format_percent
from finance_core.errors import FinanceError
from gui import dialogs, theme
from gui.app_state import AppState
from gui.dialogs import Prompts
from gui.widgets import Column, DataTable, PeriodSelector, shorten

ALL_MONTHS = "All months"


class BudgetsView(ttk.Frame):
    def __init__(self, parent: tk.Misc, app_state: AppState, prompts: Prompts) -> None:
        super().__init__(parent, padding=12)
        self.app_state = app_state
        self.prompts = prompts
        self._statuses: dict[str, BudgetStatus] = {}

        top = ttk.Frame(self)
        top.pack(fill="x")
        self.period = PeriodSelector(top, self.refresh, all_label=ALL_MONTHS, caption="Month:")
        self.period.pack(side="left")

        columns = [
            Column("category", "Category", 150, stretch=True),
            Column("month", "Month", 80),
            Column("budget", "Budget", 100, anchor="e"),
            Column("spent", "Spent", 100, anchor="e"),
            Column("remaining", "Remaining", 100, anchor="e"),
            Column("used", "Used", 80, anchor="e"),
            Column("status", "Status", 140),
        ]
        # Buttons, legend and messages are packed at the bottom first so they are never clipped.
        row = ttk.Frame(self)
        row.pack(side="bottom", fill="x", pady=(8, 0))
        self.empty_label = ttk.Label(self, text="", style="Muted.TLabel")
        self.empty_label.pack(side="bottom", anchor="w", pady=(6, 0))
        self.legend = ttk.Label(
            self, style="Muted.TLabel", wraplength=900, justify="left",
            text=(f"Within budget: under {APPROACHING_PERCENT}% used.  "
                  f"Approaching limit: {APPROACHING_PERCENT}% or more but not yet the whole budget.  "
                  "Fully used: exactly 100%.  Exceeded: over 100%.  Only expenses count."))
        self.legend.pack(side="bottom", anchor="w", pady=(6, 0))

        self.table = DataTable(self, columns, height=8, on_double_click=self.edit_selected)
        self.table.pack(fill="both", expand=True, pady=(10, 0))
        for status, (background, foreground) in theme.STATUS_COLOURS.items():
            self.table.configure_tag(status, background=background, foreground=foreground)

        ttk.Button(row, text="Add budget", style="Accent.TButton", command=self.add).pack(side="left")
        ttk.Button(row, text="Edit limit", command=self.edit_selected).pack(side="left", padx=(6, 0))
        ttk.Button(row, text="Delete budget", command=self.delete_selected).pack(side="left", padx=(6, 0))
        self.message = ttk.Label(row, text="", style="Muted.TLabel")
        self.message.pack(side="left", padx=(16, 0))
        self.refresh()

    def refresh(self) -> None:
        self.period.set_months(self.app_state.months())
        statuses = self.app_state.budgets.get_statuses(
            self.app_state.transactions.get_all_transactions(), self.period.month())
        self._statuses = {f"b{index}": status for index, status in enumerate(statuses)}
        self.table.set_rows([
            (row_id,
             (shorten(s.category, 24), s.month, format_money(s.limit), format_money(s.spent),
              format_money(s.remaining), format_percent(s.utilisation_percent), s.status),
             s.status)
            for row_id, s in self._statuses.items()
        ])
        self.empty_label.configure(
            text="" if statuses else "No budgets yet. Use Add budget to set a monthly limit.")

    def _selected(self) -> Optional[BudgetStatus]:
        row_id = self.table.selected_id()
        if row_id is None:
            self.message.configure(text="Select a budget in the list first.")
            return None
        return self._statuses[row_id]

    def add(self) -> None:
        dialogs.ask_budget(self, self.app_state)
        self.message.configure(text="")

    def edit_selected(self) -> None:
        status = self._selected()
        if status is None:
            return
        try:
            budget = self.app_state.budgets.get_budget(status.category, status.month)
        except FinanceError as error:
            self.prompts.error("Cannot edit", str(error))
            return
        dialogs.ask_budget(self, self.app_state, budget)
        self.message.configure(text="")

    def delete_selected(self) -> None:
        status = self._selected()
        if status is None:
            return
        question = (f"Delete the {status.category} budget for {status.month} "
                    f"({format_money(status.limit)})?\n\nThis cannot be undone.")
        if not self.prompts.confirm("Delete budget", question):
            return
        try:
            self.app_state.delete_budget(status.category, status.month)
            self.message.configure(text="Budget deleted.")
        except FinanceError as error:
            self.prompts.error("Could not delete", str(error))