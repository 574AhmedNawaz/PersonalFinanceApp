"""JSON persistence for transactions and budgets.

Design rules:
- A missing or empty data file is not an error: it means a fresh start.
- A corrupt file raises StorageError and is NEVER overwritten, so the
  user's data is not silently destroyed.
- Saving writes to a temporary file first and then swaps it in, so a
  crash mid-save cannot leave a half-written data file.
Transactions and budgets are kept in separate files but share the same
reading and writing helpers, so the safety rules are identical.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Callable, Iterable, TextIO

from finance_core.errors import FinanceError, StorageError
from finance_core.models import Budget, Transaction
from finance_core.validation import (
    validate_amount,
    validate_category,
    validate_date,
    validate_month,
    validate_text,
    validate_transaction_type,
)

DATA_VERSION = 1
DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DATA_FILE = DATA_FOLDER / "transactions.json"
DEFAULT_BUDGET_FILE = DATA_FOLDER / "budgets.json"
DEFAULT_EXPORT_FILE = DATA_FOLDER / "transactions_export.csv"

CSV_COLUMNS = ("Transaction ID", "Type", "Amount", "Category", "Description", "Date")


# ----- shared helpers -----

def _write_atomically(
    file_path: Path,
    write_content: Callable[[TextIO], None],
    *,
    encoding: str = "utf-8",
    newline: str | None = None,
) -> None:
    """Write a file via a temporary file so a crash cannot leave half a file.

    write_content receives the open temporary file. Only when it has
    finished is the temporary file swapped in place of the real one.
    """
    file_path = Path(file_path)
    temp_name = None
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding=encoding,
            newline=newline,
            dir=file_path.parent,
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_name = temp_file.name
            write_content(temp_file)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_name, file_path)  # atomic swap on Windows and Linux
    except OSError as error:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)
        raise StorageError(
            f"Could not save data to {file_path}: {error}. "
            "Make sure the file is not open in another program."
        ) from error


def _save_records(file_path: Path, key: str, records: list[dict]) -> None:
    """Write {"version": ..., key: records} to file_path, safely."""
    payload = {"version": DATA_VERSION, key: records}
    _write_atomically(file_path, lambda file: json.dump(payload, file, indent=2))


def _load_records(file_path: Path, key: str) -> list:
    """Read the list stored under `key`.

    Returns an empty list if the file is missing or empty.
    Raises StorageError if the file cannot be read or has the wrong shape.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return []
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise StorageError(f"Could not read {file_path}: {error}") from error
    if not text.strip():
        return []

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise StorageError(
            f"{file_path} is not valid JSON (line {error.lineno}, "
            f"column {error.colno}). The file has been left untouched; "
            "fix or rename it to continue."
        ) from error

    if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
        raise StorageError(
            f"{file_path} does not have the expected format "
            f"(a '{key}' list is missing)."
        )
    return payload[key]


# ----- transactions -----

def save_transactions(file_path: Path, transactions: Iterable[Transaction]) -> None:
    """Write all transactions to file_path as JSON, safely."""
    _save_records(file_path, "transactions", [t.to_dict() for t in transactions])


def load_transactions(file_path: Path) -> list[Transaction]:
    """Read transactions from file_path (see _load_records for the rules)."""
    transactions: list[Transaction] = []
    seen_ids: set[str] = set()  # a set gives O(1) duplicate checking
    for position, record in enumerate(_load_records(file_path, "transactions"), start=1):
        transaction = _record_to_transaction(record, position)
        if transaction.transaction_id in seen_ids:
            raise StorageError(
                f"Record {position}: duplicate transaction ID "
                f"'{transaction.transaction_id}'."
            )
        seen_ids.add(transaction.transaction_id)
        transactions.append(transaction)
    return transactions


def _record_to_transaction(record: object, position: int) -> Transaction:
    """Rebuild one Transaction from a stored record, validating as we go."""
    if not isinstance(record, dict):
        raise StorageError(f"Record {position} is not a valid transaction.")
    try:
        return Transaction(
            transaction_id=validate_text(record["transaction_id"], "Transaction ID"),
            transaction_type=validate_transaction_type(record["transaction_type"]),
            amount=validate_amount(record["amount"]),
            category=validate_category(record["category"]),
            description=validate_text(record["description"], "Description"),
            transaction_date=validate_date(record["date"]),
        )
    except KeyError as error:
        raise StorageError(
            f"Record {position} is missing the field {error}."
        ) from None
    except FinanceError as error:
        raise StorageError(f"Record {position} is invalid: {error}") from error


# ----- budgets -----

def save_budgets(file_path: Path, budgets: Iterable[Budget]) -> None:
    """Write all budgets to file_path as JSON, safely."""
    _save_records(file_path, "budgets", [b.to_dict() for b in budgets])


def load_budgets(file_path: Path) -> list[Budget]:
    """Read budgets from file_path (see _load_records for the rules)."""
    budgets: list[Budget] = []
    seen: set[tuple[str, str]] = set()
    for position, record in enumerate(_load_records(file_path, "budgets"), start=1):
        budget = _record_to_budget(record, position)
        key = (budget.category, budget.month)
        if key in seen:
            raise StorageError(
                f"Record {position}: duplicate budget for "
                f"{budget.category} in {budget.month}."
            )
        seen.add(key)
        budgets.append(budget)
    return budgets


def _record_to_budget(record: object, position: int) -> Budget:
    """Rebuild one Budget from a stored record, validating as we go."""
    if not isinstance(record, dict):
        raise StorageError(f"Record {position} is not a valid budget.")
    try:
        return Budget(
            category=validate_category(record["category"]),
            month=validate_month(record["month"]),
            limit=validate_amount(record["limit"]),
        )
    except KeyError as error:
        raise StorageError(
            f"Record {position} is missing the field {error}."
        ) from None
    except FinanceError as error:
        raise StorageError(f"Record {position} is invalid: {error}") from error


# ----- CSV export -----

def export_transactions_csv(file_path: Path, transactions: Iterable[Transaction]) -> None:
    """Write transactions to a CSV file that opens correctly in Excel.

    The file starts with a header row. It is saved with a UTF-8 byte order
    mark so Excel shows accented characters correctly.
    """
    def write_rows(file: TextIO) -> None:
        writer = csv.writer(file)
        writer.writerow(CSV_COLUMNS)
        for t in transactions:
            writer.writerow([
                t.transaction_id,
                t.transaction_type,
                t.amount,
                _spreadsheet_safe(t.category),
                _spreadsheet_safe(t.description),
                t.transaction_date.isoformat(),
            ])

    _write_atomically(file_path, write_rows, encoding="utf-8-sig", newline="")


def _spreadsheet_safe(text: str) -> str:
    """Stop spreadsheet programs treating text as a formula.

    A cell starting with = + - or @ can be run as a formula when the CSV
    is opened in Excel, so a leading apostrophe makes it plain text.
    """
    if text and text[0] in "=+-@\t\r":
        return "'" + text
    return text