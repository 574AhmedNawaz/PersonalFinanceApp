"""Command-line screens for searching, filtering and sorting transactions."""

from __future__ import annotations

from cli.context import AppContext
from cli.formatting import transactions_table
from finance_core.transaction_search import SORT_KEYS, search_transactions, sort_transactions
from finance_core.validation import (
    validate_category,
    validate_date,
    validate_transaction_type,
)


def run_search(context: AppContext) -> None:
    """Ask for any combination of criteria and show the matching transactions."""
    console = context.console
    console.say("Leave a field blank to skip it. All filled-in fields must match.")
    transaction_id = console.ask_text("Transaction ID: ")
    text = console.ask_text("Words in the description: ")
    transaction_type = console.ask_optional("Type (income/expense): ", validate_transaction_type)
    category = console.ask_optional("Category: ", validate_category)
    on_date = console.ask_optional("Exact date (YYYY-MM-DD): ", validate_date)

    start_date = end_date = None
    if on_date is None:
        start_date = console.ask_optional("From date (YYYY-MM-DD): ", validate_date)
        end_date = console.ask_optional("To date (YYYY-MM-DD): ", validate_date)

    results = search_transactions(
        context.transactions.get_all_transactions(),
        transaction_id=transaction_id,
        text=text,
        transaction_type=transaction_type,
        category=category,
        on_date=on_date,
        start_date=start_date,
        end_date=end_date,
    )
    if not results:
        console.say("No transactions match your search.")
        return
    console.say(transactions_table(results))
    console.say(f"{len(results)} transaction(s) found.")


def run_sort(context: AppContext) -> None:
    """Show all transactions in the order the user asks for."""
    console = context.console
    transactions = context.transactions.get_all_transactions()
    if not transactions:
        console.say("No transactions recorded yet.")
        return

    field = console.choose(f"Sort by ({'/'.join(SORT_KEYS)}): ", tuple(SORT_KEYS))
    order = console.choose("Order (asc/desc): ", ("asc", "desc"))
    ordered = sort_transactions(transactions, field, descending=(order == "desc"))
    console.say(transactions_table(ordered))