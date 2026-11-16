# Personal Finance and Expense Analytics Application

A desktop application for tracking income and expenses, built in Python for
the module CSC-44102 Foundations of Programming and Software Engineering.

It is delivered in two versions that share the same core logic: a
command-line application (CLI) and a Tkinter graphical application (GUI).

> **Status: work in progress (Day 3 of 5).** The shared core logic and the
> command-line version are complete and tested. The graphical version is
> planned for the next stage.

## Features

- Add, view, edit and delete income and expense transactions
- Search by ID or description; filter by type, category, date or date range
- Sort by date, amount, category or type (ascending or descending)
- Monthly budgets per category with four states: within budget,
  approaching limit (80% or more), fully used and exceeded
- Analytics: totals, net savings, savings rate, average expense, spending by
  category, month-by-month figures, highest category and largest transactions
- Export all transactions to a CSV file that opens in Excel
- Records are saved automatically after every change and reloaded on start-up
- Exact money arithmetic using `Decimal`
- Clear messages for invalid input and for missing, empty or corrupted data files

## Requirements

- Python 3.9 or newer (Windows 10/11 recommended)
- No third-party packages

## Running the command-line version

From the project folder:

```
python main.py --cli
```

Or run `python main.py` and choose option 1. Type `cancel` at any prompt to
stop what you are doing. Choose the last number in any menu to go back.

## Running the tests

```
python -m unittest
```

Add `-v` for a line per test.

## How data is stored

Records are saved as JSON in the `data` folder, created automatically:

- `data/transactions.json` holds the transactions
- `data/budgets.json` holds the budgets

Both files are written safely (to a temporary file first, then swapped into
place) and are listed in `.gitignore` so personal records are never uploaded.
If a data file is damaged the program stops with a message and leaves the file
untouched; it never overwrites it.

## Exporting to CSV

Choose **6. Export records** from the main menu. The default file is
`data/transactions_export.csv`; you can type a different path. The program asks
before overwriting an existing file and refuses to overwrite its own data files.
The export has one row per transaction with the columns Transaction ID, Type,
Amount, Category, Description and Date.

## Project structure

```
PersonalFinanceApp/
    main.py              start the application
    finance_core/        shared business logic (no user interface code)
        errors.py        custom exception types
        models.py        Transaction and Budget data models
        validation.py    input validation rules
        transaction_service.py   add / view / edit / delete
        transaction_search.py    search, filter and sort
        analytics_service.py     totals, savings, category and monthly figures
        budget_service.py        monthly budgets and status rules
        storage.py       JSON persistence and CSV export
    cli/                 the command-line interface
        cli_interface.py main menu and start-up
        console.py       prompts, menus and error handling
        context.py       the data shared by all screens
        formatting.py    tables and number formatting
        *_commands.py    one module per area (transactions, search, budgets,
                         analytics, export)
    tests/               unittest test suite
    data/                saved data (git-ignored)
    documentation/       design notes
```

