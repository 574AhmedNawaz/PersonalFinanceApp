# Personal Finance and Expense Analytics Application

A desktop application for tracking income and expenses, built in Python for
the module CSC-44102 Foundations of Programming and Software Engineering.

It is delivered in two versions that share the same core logic: a
command-line application (CLI) and a Tkinter graphical application (GUI).

> **Status: version 1.0.** The shared core logic, the command-line version and
> the graphical version are complete and tested (374 automated tests plus a
> recorded manual test table).

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

- Python 3.9 or newer (developed and tested with Python 3.14 on Windows)
- No third-party packages; Tkinter is included with the standard Python installer

## Running the command-line version

From the project folder:

```
python main.py --cli
```

Or run `python main.py` and choose option 1. Type `cancel` at any prompt to
stop what you are doing. Choose the last number in any menu to go back.

## Running the graphical version

```
python main.py --gui
```

The window has four tabs:

- **Dashboard**: total income, total expenses, net savings and savings rate,
  a bar chart of spending by category, budget alerts and the latest
  transactions. A period selector switches between all time and one month.
- **Transactions**: add income or expense, edit or delete the selected row
  (double-click also edits), search and filter by description, type, category
  and date range, and sort by clicking the column headings.
- **Budgets**: set a monthly limit per category. Rows are colour-coded as
  within budget, approaching limit, fully used or exceeded.
- **Analytics**: financial summary, spending by category, month-by-month
  figures and the five largest transactions.

Use **File > Export transactions to CSV...** (Ctrl+E) to save a spreadsheet
copy. Every change is saved automatically and all tabs update straight away.
The graphical version needs Tkinter, which is included with the standard
Python installer for Windows.

Both versions use the same `finance_core` package and the same data files, so
records added in one version appear in the other.

## Running the tests

## Testing

```
python -m unittest
```

Add `-v` for a line per test. The suite has 374 automated tests covering the
core logic, the command-line interface and the graphical interface. The
graphical tests are skipped automatically on a machine with no display.

The manual checks I ran on the command-line and graphical versions, with their
results, are recorded in [documentation/testing.md](documentation/testing.md).

## How data is stored

Records are saved as JSON in the `data` folder, created automatically:

- `data/transactions.json` holds the transactions
- `data/budgets.json` holds the budgets

Both files are written safely (to a temporary file first, then swapped into
place) and are listed in `.gitignore` so personal records are never uploaded.
If a data file is damaged the program stops with a message and leaves the file
untouched; it never overwrites it.

## Exporting to CSV

In the command-line version choose **6. Export records** from the main menu
(in the graphical version use **File > Export transactions to CSV...**). The
default file is
`data/transactions_export.csv`; you can type a different path. The program asks
before overwriting an existing file and refuses to overwrite its own data files.
The export has one row per transaction with the columns Transaction ID, Type,
Amount, Category, Description and Date.

## Design overview
## How it is designed

The program is split into layers so that the two interfaces never repeat
any business logic:

- `finance_core` holds all the rules: validation, transactions, search and
  sort, budgets, analytics and storage. It has no user interface code.
- `cli` and `gui` are thin layers that ask the user for input, call
  `finance_core`, and display the results.
- Money is stored as `Decimal` rounded to two places, never as `float`, so
  totals are exact.
- Data files are written to a temporary file first and then swapped into
  place, and a damaged file is never overwritten.
- In the graphical version, one shared state object notifies every tab when
  the data changes, so all screens stay in step.

## Known limitations

- One user and one local data file for each kind of record; no cloud sync.
- Budgets are monthly and per category; there are no recurring transactions.
- Amounts and dates follow the rules in `finance_core/validation.py`.

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
    gui/                 the Tkinter graphical interface
        gui_interface.py main window, menu bar and start-up
        app_state.py     shared data and change notifications
        form_logic.py    checking of form input (no widgets)
        dashboard_view.py, transactions_view.py,
        budgets_view.py, analytics_view.py   one module per tab
        dialogs.py       add / edit forms
        widgets.py       summary cards, bar chart, tables
        theme.py         colours and styling
    tests/               unittest test suite
    data/                saved data (git-ignored)
    documentation/        testing record
```
## Acknowlegment
This project was developed for CSC-44102 using only the Python standard
library (`tkinter`, `json`, `csv`, `decimal`, `datetime`, `unittest` and
others). I used Claude to learn how Git and GitHub work, including branches, pull requests, releases and to explain errors. I ran all the tests and manual checks myself,
and the results in `documentation/testing.md` are from my own runs.
