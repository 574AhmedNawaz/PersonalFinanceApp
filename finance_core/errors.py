"""Custom exceptions shared by the core logic and both interfaces.

Every error the application raises on purpose inherits from FinanceError,
so the CLI and GUI can catch one type and show a friendly message instead
of a raw Python traceback. Genuine programming errors (TypeError, etc.)
are deliberately NOT caught this way, so bugs are not hidden.
"""


class FinanceError(Exception):
    """Base class for all expected application errors."""


class ValidationError(FinanceError):
    """User input failed a validation rule."""


class TransactionNotFoundError(FinanceError):
    """No transaction exists with the requested ID."""


class StorageError(FinanceError):
    """A data file could not be read or written safely."""

class BudgetNotFoundError(FinanceError):
    """No budget exists for the requested category and month."""