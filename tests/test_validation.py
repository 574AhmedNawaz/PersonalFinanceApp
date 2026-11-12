import unittest
from datetime import date, datetime
from decimal import Decimal

from finance_core.errors import ValidationError
from finance_core.validation import (
    validate_amount,
    validate_category,
    validate_date,
    validate_text,
    validate_transaction_type,
)


class ValidateAmountTests(unittest.TestCase):
    def test_accepts_valid_amounts(self):
        self.assertEqual(validate_amount("12.50"), Decimal("12.50"))
        self.assertEqual(validate_amount(" 100 "), Decimal("100.00"))
        self.assertEqual(validate_amount(5), Decimal("5.00"))

    def test_smallest_and_largest_boundaries(self):
        self.assertEqual(validate_amount("0.01"), Decimal("0.01"))
        self.assertEqual(validate_amount("1000000000"), Decimal("1000000000.00"))

    def test_rejects_invalid_amounts(self):
        bad_values = [
            "",          # empty
            "   ",       # blank
            "abc",       # not a number
            "0",         # zero
            "0.00",      # zero with decimals
            "-5",        # negative
            "12.345",    # too many decimal places
            "nan",       # not a number
            "inf",       # infinite
            "1000000000.01",  # above the maximum
        ]
        for value in bad_values:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_amount(value)

    def test_no_floating_point_error(self):
        total = validate_amount("0.10") + validate_amount("0.20")
        self.assertEqual(total, Decimal("0.30"))


class ValidateDateTests(unittest.TestCase):
    def test_accepts_iso_string_and_date_objects(self):
        self.assertEqual(validate_date("2026-11-12"), date(2026, 11, 12))
        self.assertEqual(validate_date(date(2026, 1, 31)), date(2026, 1, 31))
        self.assertEqual(
            validate_date(datetime(2026, 1, 31, 9, 30)), date(2026, 1, 31)
        )

    def test_accepts_leap_day(self):
        self.assertEqual(validate_date("2028-02-29"), date(2028, 2, 29))

    def test_rejects_invalid_dates(self):
        for value in ["", "12/11/2026", "2026-13-01", "2026-02-30", "2027-02-29", "tomorrow"]:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_date(value)


class ValidateOtherFieldsTests(unittest.TestCase):
    def test_transaction_type_is_case_insensitive(self):
        self.assertEqual(validate_transaction_type(" Income "), "income")