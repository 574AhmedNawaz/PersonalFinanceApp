"""Command-line screen for financial analytics."""

from __future__ import annotations

from cli.context import AppContext
from cli.formatting import (
    category_totals_table,
    format_money,
    format_percent,
    monthly_table,
    transactions_table,
)
from finance_core.analytics_service import (
    expense_by_category,
    highest_expense_category,
    monthly_summaries,
    summarise,
    top_transactions,
    transactions_in_month,
)
from finance_core.validation import validate_month

TOP_TRANSACTION_COUNT = 5


def show_analytics(context: AppContext) -> None:
    """Report on all transactions, or on one month.

    Every figure on the screen is calculated from the same set of
    transactions, so the numbers always agree with each other.
    """
    console = context.console
    month = console.ask_optional("Month (YYYY-MM, Enter for all time): ", validate_month)

    transactions = context.transactions.get_all_transactions()
    if month is not None:
        transactions = transactions_in_month(transactions, month)
    period = month or "all time"
    if not transactions:
        console.say(f"No transactions for {period}.")
        return

    summary = summarise(transactions)
    console.say()
    console.say(f"FINANCIAL SUMMARY ({period})")
    console.say(f"  Total income:         {format_money(summary.total_income)}")
    console.say(f"  Total expenses:       {format_money(summary.total_expenses)}")
    console.say(f"  Net savings:          {format_money(summary.net_savings)}")
    console.say(
        "  Savings rate:         "
        f"{format_percent(summary.savings_rate, missing='N/A (no income)')}"
    )
    console.say(f"  Average expense:      {format_money(summary.average_expense)}")
    console.say(f"  Transactions counted: {summary.transaction_count}")

    totals = expense_by_category(transactions)
    console.say()
    console.say("SPENDING BY CATEGORY")
    console.say(category_totals_table(totals) if totals else "  No expenses in this period.")

    highest = highest_expense_category(transactions)
    if highest is not None:
        console.say()
        console.say(f"Highest spending category: {highest[0]} ({format_money(highest[1])})")

    console.say()
    console.say("MONTH BY MONTH")
    console.say(monthly_table(monthly_summaries(transactions)))

    console.say()
    console.say(f"LARGEST {TOP_TRANSACTION_COUNT} TRANSACTIONS")
    console.say(transactions_table(top_transactions(transactions, TOP_TRANSACTION_COUNT)))