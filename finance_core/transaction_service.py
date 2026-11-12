"""Transaction management: create, view, edit and delete.

This is the single place where transactions are changed. Both the CLI
and the GUI call these methods, so validation and rules are identical.
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable, Optional

from finance_core.errors import TransactionNotFoundError, ValidationError
from finance_core.models import Transaction
from finance_core.validation import (
    validate_amount,
    validate_category,
    validate_date,
    validate_text,
    validate_transaction_type,
)

ID_PATTERN = re.compile(r"^T(\d+)$")


class TransactionService:
    """Holds the transactions in memory and enforces the rules.

    Transactions are kept in a dictionary keyed by transaction ID.
    Compared with a plain list this gives O(1) lookup, edit and delete
    by ID, and duplicate IDs are impossible by construction. A dict also
    remembers insertion order, so listing transactions stays predictable.
    """

    def __init__(self, transactions: Iterable[Transaction] = ()) -> None:
        self._transactions: dict[str, Transaction] = {}
        self._last_number = 0
        for transaction in transactions:
            self._store_loaded(transaction)

    def __len__(self) -> int:
        return len(self._transactions)

    # ----- create -----

    def add_transaction(
        self,
        transaction_type: str,
        amount: object,
        category: str,
        description: str,
        transaction_date: object,
    ) -> Transaction:
        """Validate the inputs, create a transaction and store it."""
        # Validate everything first so a rejected transaction never
        # consumes an ID number.
        clean_type = validate_transaction_type(transaction_type)
        clean_amount = validate_amount(amount)
        clean_category = validate_category(category)
        clean_description = validate_text(description, "Description")
        clean_date = validate_date(transaction_date)

        transaction = Transaction(
            transaction_id=self._next_id(),
            transaction_type=clean_type,
            amount=clean_amount,
            category=clean_category,
            description=clean_description,
            transaction_date=clean_date,
        )
        self._transactions[transaction.transaction_id] = transaction
        return transaction

    # ----- read -----

    def get_transaction(self, transaction_id: str) -> Transaction:
        """Return one transaction or raise TransactionNotFoundError."""
        key = self._normalise_id(transaction_id)
        try:
            return self._transactions[key]
        except KeyError:
            raise TransactionNotFoundError(
                f"No transaction found with ID '{key}'."
            ) from None

    def get_all_transactions(self) -> list[Transaction]:
        """Return a new list of all transactions (oldest added first)."""
        return list(self._transactions.values())

    # ----- update -----

    def edit_transaction(
        self,
        transaction_id: str,
        *,
        transaction_type: Optional[str] = None,
        amount: Optional[object] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        transaction_date: Optional[object] = None,
    ) -> Transaction:
        """Change only the fields that are supplied.

        Every supplied value is validated first. If any value is invalid
        nothing is changed, because the stored transaction is replaced
        only after all checks have passed.
        """
        current = self.get_transaction(transaction_id)
        changes: dict[str, object] = {}
        if transaction_type is not None:
            changes["transaction_type"] = validate_transaction_type(transaction_type)
        if amount is not None:
            changes["amount"] = validate_amount(amount)
        if category is not None:
            changes["category"] = validate_category(category)
        if description is not None:
            changes["description"] = validate_text(description, "Description")
        if transaction_date is not None:
            changes["transaction_date"] = validate_date(transaction_date)

        updated = replace(current, **changes)
        self._transactions[updated.transaction_id] = updated
        return updated

    # ----- delete -----

    def delete_transaction(self, transaction_id: str) -> Transaction:
        """Remove a transaction and return it."""
        removed = self.get_transaction(transaction_id)
        del self._transactions[removed.transaction_id]
        return removed

    # ----- helpers -----

    @staticmethod
    def _normalise_id(transaction_id: str) -> str:
        return str(transaction_id).strip().upper()

    def _next_id(self) -> str:
        """Create the next ID: T0001, T0002, ...

        The counter never goes backwards while the program runs, so the
        ID of a deleted transaction is not reused in the same session.
        """
        self._last_number += 1
        return f"T{self._last_number:04d}"

    def _store_loaded(self, transaction: Transaction) -> None:
        """Add a transaction read from storage and keep the counter ahead."""
        if transaction.transaction_id in self._transactions:
            raise ValidationError(
                f"Duplicate transaction ID '{transaction.transaction_id}'."
            )
        self._transactions[transaction.transaction_id] = transaction
        match = ID_PATTERN.match(transaction.transaction_id)
        if match:
            self._last_number = max(self._last_number, int(match.group(1)))