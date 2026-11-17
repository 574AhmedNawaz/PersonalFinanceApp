"""The graphical application: main window, menus and start-up."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from finance_core.errors import FinanceError, StorageError
from finance_core.storage import DEFAULT_BUDGET_FILE, DEFAULT_DATA_FILE, DEFAULT_EXPORT_FILE
from gui import theme
from gui.analytics_view import AnalyticsView
from gui.app_state import AppState
from gui.budgets_view import BudgetsView
from gui.dashboard_view import DashboardView
from gui.dialogs import Prompts
from gui.transactions_view import TransactionsView

TITLE = "Personal Finance Manager"


def ask_save_path() -> str:
    """Show the system 'Save as' window. Returns '' if the user cancels."""
    return filedialog.asksaveasfilename(
        title="Export transactions to CSV",
        defaultextension=".csv",
        filetypes=[("CSV files (open in Excel)", "*.csv"), ("All files", "*.*")],
        initialdir=str(DEFAULT_EXPORT_FILE.parent) if DEFAULT_EXPORT_FILE.parent.exists() else None,
        initialfile=DEFAULT_EXPORT_FILE.name,
    )


class FinanceApp:
    """The main window: four tabs, a menu bar and a status line.

    Every tab reads from the same AppState, and the tabs refresh
    themselves whenever the data changes.
    """

    def __init__(
        self,
        root: tk.Tk,
        app_state: AppState,
        prompts: Optional[Prompts] = None,
        save_path_chooser: Callable[[], str] = ask_save_path,
    ) -> None:
        self.root = root
        self.app_state = app_state
        self.prompts = prompts or Prompts()
        self.save_path_chooser = save_path_chooser

        theme.apply_theme(root)
        root.title(TITLE)
        root.geometry("1100x690")
        root.minsize(960, 620)

        self._build_menu()
        self.status = ttk.Label(root, text="Your data is saved automatically after every change.",
                                style="Status.TLabel", anchor="w")
        self.status.pack(side="bottom", fill="x")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self.dashboard = DashboardView(self.notebook, app_state)
        self.transactions_view = TransactionsView(self.notebook, app_state, self.prompts)
        self.budgets_view = BudgetsView(self.notebook, app_state, self.prompts)
        self.analytics_view = AnalyticsView(self.notebook, app_state)
        for view, name in ((self.dashboard, "Dashboard"), (self.transactions_view, "Transactions"),
                           (self.budgets_view, "Budgets"), (self.analytics_view, "Analytics")):
            self.notebook.add(view, text=name)

        app_state.subscribe(self.data_changed)
        root.bind("<Control-e>", lambda event: self.export_csv())

    # ----- menu -----

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Export transactions to CSV...", accelerator="Ctrl+E",
                              command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.configure(menu=menubar)

    def show_about(self) -> None:
        self.prompts.info(
            "About",
            "Personal Finance and Expense Analytics\n\n"
            "CSC-44102 coursework. The graphical and command-line versions "
            "share the same core logic.")

    # ----- reacting to changes -----

    def refresh_all(self) -> None:
        for view in (self.dashboard, self.transactions_view, self.budgets_view, self.analytics_view):
            view.refresh()

    def data_changed(self) -> None:
        self.refresh_all()
        self.set_status(f"Saved at {datetime.now():%H:%M:%S}.")

    def set_status(self, text: str) -> None:
        self.status.configure(text=text)

    # ----- export -----

    def export_csv(self) -> None:
        if not self.app_state.transactions.get_all_transactions():
            self.prompts.info("Export", "There are no transactions to export.")
            return
        chosen = self.save_path_chooser()
        if not chosen:
            return
        try:
            count = self.app_state.export_csv(Path(chosen))
        except FinanceError as error:
            self.prompts.error("Export failed", str(error))
            return
        self.set_status(f"Exported {count} transaction(s) to {chosen}")
        self.prompts.info("Export complete", f"Exported {count} transaction(s) to:\n{chosen}")


def run_gui(transactions_file: Path = DEFAULT_DATA_FILE, budgets_file: Path = DEFAULT_BUDGET_FILE) -> int:
    """Open the window. Returns 0 on a normal exit and 1 if it could not start."""
    try:
        app_state = AppState(transactions_file, budgets_file)
    except StorageError as error:
        print(f"The application could not start: {error}")
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("The application could not start", str(error))
            root.destroy()
        except tk.TclError:
            pass
        return 1

    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"The graphical version could not open a window: {error}")
        return 1
    FinanceApp(root, app_state)
    root.mainloop()
    return 0