"""Command-line screens for managing monthly budgets."""

from __future__ import annotations

from cli.context import AppContext
from cli.formatting import budgets_table, format_money
from finance_core.budget_service import APPROACHING_PERCENT
from finance_core.validation import validate_amount, validate_category, validate_month


def budget_menu(context: AppContext) -> None:
    context.console.run_menu(
        "BUDGETS",
        [
            ("Create a budget", lambda: create_budget(context)),
            ("View budgets and spending", lambda: view_budgets(context)),
            ("Edit a budget limit", lambda: edit_budget(context)),
            ("Delete a budget", lambda: delete_budget(context)),
        ],
    )


def create_budget(context: AppContext) -> None:
    console = context.console
    category = console.ask("Category: ", validate_category)
    month = console.ask("Month (YYYY-MM): ", validate_month)
    limit = console.ask("Budget limit for the month: ", validate_amount)

    budget = context.budgets.create_budget(category, month, limit)
    context.save_budgets()
    console.say(
        f"Budget created: {budget.category}, {budget.month}, "
        f"limit {format_money(budget.limit)}."
    )


def view_budgets(context: AppContext) -> None:
    console = context.console
    month = console.ask_optional("Month (YYYY-MM, Enter for all): ", validate_month)
    statuses = context.budgets.get_statuses(context.transactions.get_all_transactions(), month)
    if not statuses:
        console.say("No budgets found.")
        return

    console.say(budgets_table(statuses))
    console.say(f"Within budget: under {APPROACHING_PERCENT}% used.")
    console.say(f"Approaching limit: {APPROACHING_PERCENT}% or more, but not yet the full budget.")
    console.say("Fully used: exactly 100%.  Exceeded: over 100%.  Only expenses count.")


def edit_budget(context: AppContext) -> None:
    console = context.console
    category = console.ask("Category of the budget to edit: ", validate_category)
    month = console.ask("Month (YYYY-MM): ", validate_month)
    current = context.budgets.get_budget(category, month)
    new_limit = console.ask(f"New limit [{format_money(current.limit)}]: ", validate_amount)

    updated = context.budgets.edit_budget(category, month, new_limit)
    context.save_budgets()
    console.say(f"Budget updated: limit is now {format_money(updated.limit)}.")


def delete_budget(context: AppContext) -> None:
    console = context.console
    category = console.ask("Category of the budget to delete: ", validate_category)
    month = console.ask("Month (YYYY-MM): ", validate_month)
    budget = context.budgets.get_budget(category, month)
    if not console.confirm(
        f"Delete the {budget.category} budget for {budget.month} "
        f"({format_money(budget.limit)})?"
    ):
        console.say("Nothing was deleted.")
        return

    context.budgets.delete_budget(category, month)
    context.save_budgets()
    console.say("Budget deleted.")