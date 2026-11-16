"""Command-line screens for adding, viewing, editing and deleting transactions."""

from __future__ import annotations

from datetime import date

from cli.context import AppContext
from cli.formatting import format_money, transactions_table
from finance_core.models import EXPENSE, INCOME
from finance_core.validation import (
    validate_amount,
    validate_category,
    validate_date,
    validate_text,
    validate_transaction_type,
)


def _validate_description(value: str) -> str:
    return validate_text(value, "Description")


def transaction_menu(context: AppContext) -> None:
    context.console.run_menu(
        "TRANSACTIONS",
        [
            ("Add income", lambda: add_transaction(context, INCOME)),
            ("Add expense", lambda: add_transaction(context, EXPENSE)),
            ("View all transactions", lambda: view_transactions(context)),
            ("Edit a transaction", lambda: edit_transaction(context)),
            ("Delete a transaction", lambda: delete_transaction(context)),
        ],
    )


def add_transaction(context: AppContext, transaction_type: str) -> None:
    console = context.console
    amount = console.ask("Amount: ", validate_amount)
    category = console.ask("Category: ", validate_category)
    description = console.ask("Description: ", _validate_description)
    day = console.ask_optional("Date (YYYY-MM-DD, Enter for today): ", validate_date)

    transaction = context.transactions.add_transaction(
        transaction_type, amount, category, description, day or date.today()
    )
    context.save_transactions()
    console.say(
        f"Added {transaction.transaction_type} {transaction.transaction_id}: "
        f"{format_money(transaction.amount)} ({transaction.category}) "
        f"on {transaction.transaction_date.isoformat()}."
    )


def view_transactions(context: AppContext) -> None:
    transactions = context.transactions.get_all_transactions()
    if not transactions:
        context.console.say("No transactions recorded yet.")
        return
    context.console.say(transactions_table(transactions))
    context.console.say(f"{len(transactions)} transaction(s).")


def edit_transaction(context: AppContext) -> None:
    console = context.console
    current = context.transactions.get_transaction(console.ask_text("Transaction ID to edit: "))
    console.say(transactions_table([current]))
    console.say("Press Enter to keep the current value.")

    answers = {
        "transaction_type": console.ask_optional(
            f"Type [{current.transaction_type}]: ", validate_transaction_type
        ),
        "amount": console.ask_optional(f"Amount [{current.amount}]: ", validate_amount),
        "category": console.ask_optional(f"Category [{current.category}]: ", validate_category),
        "description": console.ask_optional(
            f"Description [{current.description}]: ", _validate_description
        ),
        "transaction_date": console.ask_optional(
            f"Date [{current.transaction_date.isoformat()}]: ", validate_date
        ),
    }
    changes = {field: value for field, value in answers.items() if value is not None}
    if not changes:
        console.say("Nothing was changed.")
        return

    updated = context.transactions.edit_transaction(current.transaction_id, **changes)
    context.save_transactions()
    console.say("Updated:")
    console.say(transactions_table([updated]))


def delete_transaction(context: AppContext) -> None:
    console = context.console
    transaction = context.transactions.get_transaction(
        console.ask_text("Transaction ID to delete: ")
    )
    console.say(transactions_table([transaction]))
    if not console.confirm("Delete this transaction?"):
        console.say("Nothing was deleted.")
        return

    context.transactions.delete_transaction(transaction.transaction_id)
    context.save_transactions()
    console.say(f"Deleted {transaction.transaction_id}.")