"""The Transactions tab: filter, sort, add, edit and delete."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from finance_core.display import format_money
from finance_core.errors import FinanceError
from finance_core.models import EXPENSE, INCOME
from finance_core.transaction_search import SORT_KEYS, search_transactions, sort_transactions
from gui import dialogs, theme
from gui.app_state import AppState
from gui.dialogs import Prompts
from gui.form_logic import ANY, check_filter_form
from gui.widgets import Column, DataTable, shorten

# Table columns that can be sorted by clicking their heading.
SORTABLE = {"date": "Date", "type": "Type", "category": "Category", "amount": "Amount"}


class TransactionsView(ttk.Frame):
    def __init__(self, parent: tk.Misc, app_state: AppState, prompts: Prompts) -> None:
        super().__init__(parent, padding=12)
        self.app_state = app_state
        self.prompts = prompts
        self.sort_key = "date"
        self.descending = True  # newest first

        self._build_filter_bar()
        self._build_buttons()      # packed at the bottom first, so they are never pushed out of view
        self._build_table()
        self.refresh()

    # ----- layout -----

    def _build_filter_bar(self) -> None:
        bar = ttk.LabelFrame(self, text="Search and filter", padding=8)
        bar.pack(fill="x")
        self.text_var = tk.StringVar()
        self.type_var = tk.StringVar(value=ANY)
        self.category_var = tk.StringVar()
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()

        ttk.Label(bar, text="Description contains").grid(row=0, column=0, sticky="w")
        ttk.Label(bar, text="Type").grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Label(bar, text="Category").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Label(bar, text="From (YYYY-MM-DD)").grid(row=0, column=3, sticky="w", padx=(10, 0))
        ttk.Label(bar, text="To (YYYY-MM-DD)").grid(row=0, column=4, sticky="w", padx=(10, 0))

        self.text_entry = ttk.Entry(bar, textvariable=self.text_var, width=18)
        self.type_combo = ttk.Combobox(bar, textvariable=self.type_var, state="readonly", width=9,
                                       values=[ANY, INCOME, EXPENSE])
        self.category_combo = ttk.Combobox(bar, textvariable=self.category_var, width=14)
        self.start_entry = ttk.Entry(bar, textvariable=self.start_var, width=12)
        self.end_entry = ttk.Entry(bar, textvariable=self.end_var, width=12)
        self.text_entry.grid(row=1, column=0, sticky="w")
        self.type_combo.grid(row=1, column=1, sticky="w", padx=(10, 0))
        self.category_combo.grid(row=1, column=2, sticky="w", padx=(10, 0))
        self.start_entry.grid(row=1, column=3, sticky="w", padx=(10, 0))
        self.end_entry.grid(row=1, column=4, sticky="w", padx=(10, 0))
        ttk.Button(bar, text="Apply", style="Accent.TButton", command=self.refresh).grid(
            row=1, column=5, padx=(10, 0))
        ttk.Button(bar, text="Clear", command=self.clear_filters).grid(row=1, column=6, padx=(6, 0))

        self.filter_error = ttk.Label(bar, text="", style="Error.TLabel")
        self.filter_error.grid(row=2, column=0, columnspan=7, sticky="w", pady=(6, 0))
        for widget in (self.text_entry, self.start_entry, self.end_entry, self.category_combo):
            widget.bind("<Return>", lambda event: self.refresh())
        self.type_combo.bind("<<ComboboxSelected>>", lambda event: self.refresh())

    def _build_table(self) -> None:
        columns = [
            Column("id", "ID", 70),
            Column("date", "Date", 100),
            Column("type", "Type", 80),
            Column("category", "Category", 140),
            Column("description", "Description", 280, stretch=True),
            Column("amount", "Amount", 110, anchor="e"),
        ]
        self.table = DataTable(self, columns, height=8, on_heading_click=self.sort_by,
                               on_double_click=self.edit_selected)
        self.table.pack(fill="both", expand=True, pady=(10, 0))
        self.table.configure_tag(INCOME, foreground=theme.INCOME)
        self.table.configure_tag(EXPENSE, foreground=theme.EXPENSE)

    def _build_buttons(self) -> None:
        row = ttk.Frame(self)
        row.pack(side="bottom", fill="x", pady=(8, 0))
        self.summary = ttk.Label(self, text="", style="Muted.TLabel")
        self.summary.pack(side="bottom", anchor="w", pady=(6, 0))
        ttk.Button(row, text="Add income", command=lambda: self.add(INCOME)).pack(side="left")
        ttk.Button(row, text="Add expense", style="Accent.TButton",
                   command=lambda: self.add(EXPENSE)).pack(side="left", padx=(6, 0))
        ttk.Button(row, text="Edit selected", command=self.edit_selected).pack(side="left", padx=(18, 0))
        ttk.Button(row, text="Delete selected", command=self.delete_selected).pack(side="left", padx=(6, 0))
        self.message = ttk.Label(row, text="", style="Muted.TLabel")
        self.message.pack(side="left", padx=(16, 0))

    # ----- showing the data -----

    def current_filters(self):
        return check_filter_form(self.text_var.get(), self.type_var.get(), self.category_var.get(),
                                 self.start_var.get(), self.end_var.get())

    def refresh(self) -> None:
        """Re-read the data and show the rows that match the filters."""
        self.category_combo.configure(values=self.app_state.categories())
        filters = self.current_filters()
        if not filters.ok:
            self.filter_error.configure(text="  ".join(filters.errors.values()))
            return
        self.filter_error.configure(text="")

        everything = self.app_state.transactions.get_all_transactions()
        matches = search_transactions(
            everything,
            text=filters.values["text"],
            transaction_type=filters.values["transaction_type"],
            category=filters.values["category"],
            start_date=filters.values["start_date"],
            end_date=filters.values["end_date"],
        )
        ordered = sort_transactions(matches, self.sort_key, self.descending)
        self.table.set_rows([
            (t.transaction_id,
             (t.transaction_id, t.transaction_date.isoformat(), t.transaction_type, t.category,
              shorten(t.description, 60), format_money(t.amount)),
             t.transaction_type)
            for t in ordered
        ])
        self._update_headings()
        if not everything:
            self.summary.configure(text="No transactions yet. Use Add income or Add expense to start.")
        elif not ordered:
            self.summary.configure(text="No transactions match the filters.")
        else:
            self.summary.configure(text=f"Showing {len(ordered)} of {len(everything)} transaction(s).")

    def clear_filters(self) -> None:
        for variable, value in ((self.text_var, ""), (self.type_var, ANY), (self.category_var, ""),
                                (self.start_var, ""), (self.end_var, "")):
            variable.set(value)
        self.refresh()

    def sort_by(self, key: str) -> None:
        """Sort by a column; clicking the same column again reverses the order."""
        if key not in SORT_KEYS:
            return  # ID and Description cannot be sorted
        if key == self.sort_key:
            self.descending = not self.descending
        else:
            self.sort_key, self.descending = key, False
        self.refresh()

    def _update_headings(self) -> None:
        for key, name in SORTABLE.items():
            arrow = ""
            if key == self.sort_key:
                arrow = "  \u25bc" if self.descending else "  \u25b2"
            self.table.set_heading(key, name + arrow)

    # ----- actions -----

    def add(self, transaction_type: str) -> None:
        dialogs.ask_transaction(self, self.app_state, default_type=transaction_type)
        self.message.configure(text="")

    def _selected(self) -> Optional[str]:
        selected = self.table.selected_id()
        if selected is None:
            self.message.configure(text="Select a transaction in the list first.")
        return selected

    def edit_selected(self) -> None:
        transaction_id = self._selected()
        if transaction_id is None:
            return
        try:
            transaction = self.app_state.transactions.get_transaction(transaction_id)
        except FinanceError as error:
            self.prompts.error("Cannot edit", str(error))
            return
        dialogs.ask_transaction(self, self.app_state, transaction)
        self.message.configure(text="")

    def delete_selected(self) -> None:
        transaction_id = self._selected()
        if transaction_id is None:
            return
        try:
            transaction = self.app_state.transactions.get_transaction(transaction_id)
            question = (f"Delete {transaction.transaction_id}: {transaction.transaction_type} of "
                        f"{format_money(transaction.amount)} ({transaction.category}) on "
                        f"{transaction.transaction_date.isoformat()}?\n\nThis cannot be undone.")
            if not self.prompts.confirm("Delete transaction", question):
                return
            self.app_state.delete_transaction(transaction_id)
            self.message.configure(text=f"Deleted {transaction_id}.")
        except FinanceError as error:
            self.prompts.error("Could not delete", str(error))