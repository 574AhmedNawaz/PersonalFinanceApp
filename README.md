# Personal Finance and Expense Analytics Application

A desktop application for tracking income and expenses, built in Python for
the module CSC-44102 Foundations of Programming and Software Engineering.

It will be delivered in two versions that share the same core logic:
a command-line application (CLI) and a Tkinter graphical application (GUI).

> **Status: work in progress (Day 1 of 5).** The transaction core and JSON
> storage are implemented and tested. Search, sorting, budgets, analytics,
> the CLI and the GUI are planned for the following days.

## Features so far

- Add, view, edit and delete income and expense transactions
- Shared input validation (amounts, dates, categories, descriptions)
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
        models.py        Transaction data model
        validation.py    input validation rules
        transaction_service.py   add / view / edit / delete
        storage.py       JSON persistence
    tests/               unittest test suite
    data/                saved data (transactions.json is git-ignored)
    documentation/       design notes
```

## Acknowledgements

*(To be completed: list any tools, libraries, references and assistance used,
following the module's academic integrity guidance.)*