"""The command-line application: loads the saved data and shows the main menu."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from cli.analytics_commands import show_analytics
from cli.budget_commands import budget_menu
from cli.console import Console
from cli.context import AppContext
from cli.export_commands import export_records
from cli.search_commands import run_search, run_sort
from cli.transaction_commands import transaction_menu
from finance_core.budget_service import BudgetService
from finance_core.storage import load_budgets, load_transactions
from finance_core.transaction_service import TransactionService


class CommandLineApp:
    """Ties the screens together around one shared set of data.

    Creating the app loads the saved files. If a file is corrupted a
    StorageError is raised before anything is shown, so the damaged file
    is never overwritten.
    """

    def __init__(
        self,
        transactions_file: Path,
        budgets_file: Path,
        export_file: Path,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
    ) -> None:
        self.context = AppContext(
            console=Console(input_func, output_func),
            transactions=TransactionService(load_transactions(transactions_file)),
            budgets=BudgetService(load_budgets(budgets_file)),
            transactions_file=transactions_file,
            budgets_file=budgets_file,
            export_file=export_file,
        )

    def run(self) -> None:
        console = self.context.console
        context = self.context
        console.say("=== Personal Finance Manager ===")
        console.say("Type 'cancel' at any prompt to stop what you are doing.")
        try:
            console.run_menu(
                "MAIN MENU",
                [
                    ("Transaction management", lambda: transaction_menu(context)),
                    ("Search and filtering", lambda: run_search(context)),
                    ("Sorting", lambda: run_sort(context)),
                    ("Budget management", lambda: budget_menu(context)),
                    ("Financial analytics", lambda: show_analytics(context)),
                    ("Export records", lambda: export_records(context)),
                ],
                leave_label="Exit",
            )
        except (EOFError, KeyboardInterrupt):
            console.say()
            console.say("Input ended. Your data has already been saved.")
            return
        console.say("Goodbye! Your data has been saved.")