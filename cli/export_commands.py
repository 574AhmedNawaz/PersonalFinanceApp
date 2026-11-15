"""Command-line screen for exporting transactions to a CSV file."""

from __future__ import annotations

from pathlib import Path

from cli.context import AppContext
from finance_core.errors import ValidationError
from finance_core.storage import export_transactions_csv


def export_records(context: AppContext) -> None:
    console = context.console
    transactions = context.transactions.get_all_transactions()
    if not transactions:
        console.say("There are no transactions to export.")
        return

    answer = console.ask_text(f"File to create [{context.export_file}]: ").strip('"')
    path = Path(answer) if answer else context.export_file

    if _is_data_file(context, path):
        raise ValidationError(
            "That file holds your saved data. Choose a different file name for the export."
        )
    if path.exists() and not console.confirm(f"{path} already exists. Overwrite it?"):
        console.say("Export cancelled. The existing file was not changed.")
        return

    export_transactions_csv(path, transactions)
    console.say(f"Exported {len(transactions)} transaction(s) to {path}")


def _is_data_file(context: AppContext, path: Path) -> bool:
    """True if path is one of the program's own data files.

    Exporting to one of them would destroy the saved records.
    """
    protected = {context.transactions_file.resolve(), context.budgets_file.resolve()}
    return path.resolve() in protected