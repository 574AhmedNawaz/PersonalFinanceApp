"""Pop-up forms for transactions and budgets, plus message boxes."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from typing import Callable, Optional

from finance_core.errors import FinanceError
from finance_core.models import EXPENSE, INCOME, TRANSACTION_TYPES, Budget, Transaction
from gui.app_state import AppState
from gui.form_logic import check_budget_form, check_transaction_form


class Prompts:
    """Message boxes. Tests replace this class so no window blocks them."""

    def confirm(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, icon="warning")

    def error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)


class _FormDialog(tk.Toplevel):
    """A small modal form: labelled fields, an error line under each, Save and Cancel.

    Subclasses list their fields in build_fields() and say what Save does
    in save(). The form shows every problem at once, next to its field.
    """

    heading = ""

    def __init__(self, parent: tk.Misc, state: AppState) -> None:
        super().__init__(parent)
        self.app_state = state
        self.result: Optional[object] = None
        self.vars: dict[str, tk.StringVar] = {}
        self.widgets: dict[str, ttk.Widget] = {}
        self._error_labels: dict[str, ttk.Label] = {}
        self._next_row = 0

        self.title(self.heading)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())

        self.body = ttk.Frame(self, padding=16)
        self.body.pack(fill="both", expand=True)
        self.build_fields()

        self.form_error = ttk.Label(self.body, text="", style="Error.TLabel", wraplength=340)
        self.form_error.grid(row=self._next_row, column=0, columnspan=2, sticky="w", pady=(4, 0))
        buttons = ttk.Frame(self.body)
        buttons.grid(row=self._next_row + 1, column=0, columnspan=2, sticky="e", pady=(12, 0))
        self.cancel_button = ttk.Button(buttons, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side="right")
        self.save_button = ttk.Button(buttons, text="Save", style="Accent.TButton", command=self.submit)
        self.save_button.pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda event: self.submit())
        self.bind("<Escape>", lambda event: self.destroy())

    # ----- building the form -----

    def build_fields(self) -> None:
        raise NotImplementedError

    def add_field(self, key: str, label: str, make_widget: Callable[[ttk.Frame, tk.StringVar], ttk.Widget],
                  initial: str = "") -> None:
        variable = tk.StringVar(value=initial)
        self.vars[key] = variable
        ttk.Label(self.body, text=label).grid(row=self._next_row, column=0, sticky="w",
                                              padx=(0, 12), pady=(6, 0))
        widget = make_widget(self.body, variable)
        widget.grid(row=self._next_row, column=1, sticky="ew", pady=(6, 0))
        self.widgets[key] = widget
        error = ttk.Label(self.body, text="", style="Error.TLabel", wraplength=300)
        error.grid(row=self._next_row + 1, column=1, sticky="w")
        self._error_labels[key] = error
        self._next_row += 2

    def entry(self, parent: ttk.Frame, variable: tk.StringVar) -> ttk.Entry:
        return ttk.Entry(parent, textvariable=variable, width=32)

    def combo(
        self, values: list[str], readonly: bool = False
    ) -> Callable[[ttk.Frame, tk.StringVar], ttk.Widget]:
        def make(parent: ttk.Frame, variable: tk.StringVar) -> ttk.Combobox:
            return ttk.Combobox(parent, textvariable=variable, values=values, width=30,
                                state="readonly" if readonly else "normal")
        return make

    # ----- showing problems -----

    def show_errors(self, errors: dict[str, str]) -> None:
        for key, label in self._error_labels.items():
            label.configure(text=errors.get(key, ""))
        self.form_error.configure(text="")

    @property
    def error_texts(self) -> dict[str, str]:
        """The message currently shown for each field that has one."""
        return {key: str(label.cget("text")) for key, label in self._error_labels.items()
                if str(label.cget("text"))}

    # ----- saving -----

    def submit(self) -> bool:
        """Check the form and save. Returns True if the dialog was saved and closed."""
        try:
            saved = self.save()
        except FinanceError as error:
            self.form_error.configure(text=str(error))
            return False
        if saved is None:
            return False
        self.result = saved
        self.destroy()
        return True

    def save(self) -> Optional[object]:
        raise NotImplementedError


class TransactionDialog(_FormDialog):
    """Add a transaction, or edit an existing one."""

    def __init__(self, parent: tk.Misc, state: AppState, transaction: Optional[Transaction] = None,
                 default_type: str = EXPENSE) -> None:
        self.transaction = transaction
        self.default_type = default_type
        self.heading = "Edit transaction" if transaction else (
            "Add income" if default_type == INCOME else "Add expense")
        super().__init__(parent, state)

    def build_fields(self) -> None:
        t = self.transaction
        self.add_field("transaction_type", "Type", self.combo(list(TRANSACTION_TYPES), readonly=True),
                       t.transaction_type if t else self.default_type)
        self.add_field("amount", "Amount", self.entry, str(t.amount) if t else "")
        self.add_field("category", "Category", self.combo(self.app_state.categories()),
                       t.category if t else "")
        self.add_field("description", "Description", self.entry, t.description if t else "")
        initial_date = t.transaction_date if t else date.today()
        self.add_field("transaction_date", "Date (YYYY-MM-DD)", self.entry, initial_date.isoformat())

    def save(self) -> Optional[Transaction]:
        result = check_transaction_form(*(self.vars[key].get() for key in (
            "transaction_type", "amount", "category", "description", "transaction_date")))
        self.show_errors(result.errors)
        if not result.ok:
            return None
        if self.transaction is None:
            return self.app_state.add_transaction(**result.values)
        return self.app_state.edit_transaction(self.transaction.transaction_id, **result.values)


class BudgetDialog(_FormDialog):
    """Create a budget, or change the limit of an existing one.

    A budget is identified by its category and month, so when editing,
    those two fields are shown but cannot be changed.
    """

    def __init__(self, parent: tk.Misc, state: AppState, budget: Optional[Budget] = None) -> None:
        self.budget = budget
        self.heading = "Edit budget limit" if budget else "Create budget"
        super().__init__(parent, state)

    def build_fields(self) -> None:
        b = self.budget
        self.add_field("category", "Category", self.combo(self.app_state.categories()),
                       b.category if b else "")
        self.add_field("month", "Month (YYYY-MM)", self.entry,
                       b.month if b else date.today().strftime("%Y-%m"))
        self.add_field("limit", "Monthly limit", self.entry, str(b.limit) if b else "")
        if b is not None:
            self.widgets["category"].state(["disabled"])
            self.widgets["month"].state(["disabled"])

    def save(self) -> Optional[Budget]:
        result = check_budget_form(*(self.vars[key].get() for key in ("category", "month", "limit")))
        self.show_errors(result.errors)
        if not result.ok:
            return None
        values = result.values
        if self.budget is None:
            return self.app_state.create_budget(values["category"], values["month"], values["limit"])
        return self.app_state.edit_budget(self.budget.category, self.budget.month, values["limit"])


def _show_modal(dialog: _FormDialog, parent: tk.Misc) -> None:
    """Centre the dialog over its window and wait until it is closed."""
    dialog.update_idletasks()
    top = parent.winfo_toplevel()
    x = top.winfo_rootx() + (top.winfo_width() - dialog.winfo_width()) // 2
    y = top.winfo_rooty() + (top.winfo_height() - dialog.winfo_height()) // 3
    dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    dialog.grab_set()
    first = next(iter(dialog.widgets.values()))
    first.focus_set()
    dialog.wait_window()


def ask_transaction(parent: tk.Misc, state: AppState, transaction: Optional[Transaction] = None,
                    default_type: str = EXPENSE) -> Optional[Transaction]:
    """Show the transaction form. Returns the saved transaction, or None if cancelled."""
    dialog = TransactionDialog(parent, state, transaction, default_type)
    _show_modal(dialog, parent)
    return dialog.result  # type: ignore[return-value]


def ask_budget(parent: tk.Misc, state: AppState, budget: Optional[Budget] = None) -> Optional[Budget]:
    """Show the budget form. Returns the saved budget, or None if cancelled."""
    dialog = BudgetDialog(parent, state, budget)
    _show_modal(dialog, parent)
    return dialog.result  # type: ignore[return-value]