# Personal Finance and Expense Analytics Application

A desktop application for tracking income and expenses, built in Python for
the module CSC-44102 Foundations of Programming and Software Engineering.

It will be delivered in two versions that share the same core logic:
a command-line application (CLI) and a Tkinter graphical application (GUI).

> **Status: work in progress (Day 2 of 5).** The shared core logic is complete
> and tested: transactions, search, sorting, budgets, analytics and JSON
> storage. The CLI and the GUI are planned for the following days.

## Features so far

- Add, view, edit and delete income and expense transactions
- Search by ID or description; filter by type, category, date or date range
- Sort by date, amount, category or type (ascending or descending)
- Monthly budgets per category with four states: within budget,
  approaching limit (80% or more), fully used and exceeded
- Analytics: totals, net savings, savings rate, average expense, spending by
  category, monthly summaries, highest category and top transactions
- Shared input validation (amounts, dates, months, categories, descriptions)
- Exact money arithmetic using `Decimal`
- Safe JSON saving and loading (temporary file + atomic replace)
- Clear errors for missing, empty or corrupted data files

## Requirements

- Python 3.9 or newer (Windows 10/11 recommended)
- No third-party packages

## Running the tests

From the project folder:

```
python -m unittest -v
```

## Project structure

```
PersonalFinanceApp/
    finance_core/        shared business logic (no user interface code)
        errors.py        custom exception types
        models.py        Transaction and Budget data models
        validation.py    input validation rules
        transaction_service.py   add / view / edit / delete
        transaction_search.py    search, filter and sort
        analytics_service.py     totals, savings, category and monthly figures
        budget_service.py        monthly budgets and status rules
        storage.py       JSON persistence for transactions and budgets
    tests/               unittest test suite
    data/                saved data (transactions.json and budgets.json are git-ignored)
    documentation/       design notes
```

## Acknowledgements

*(To be completed: list any tools, libraries, references and assistance used,
following the module's academic integrity guidance.)*