import unittest

from cli.console import Cancelled, Console
from finance_core.errors import StorageError, ValidationError
from finance_core.validation import validate_amount


def scripted_console(*answers):
    """A Console fed from a list of answers; returns (console, printed_lines)."""
    remaining = iter(answers)
    lines = []
    console = Console(input_func=lambda prompt="": next(remaining), output_func=lines.append)
    return console, lines


class AskTests(unittest.TestCase):
    def test_ask_returns_a_valid_answer(self):
        console, _ = scripted_console("12.5")
        self.assertEqual(str(console.ask("Amount: ", validate_amount)), "12.50")

    def test_ask_repeats_until_valid_and_shows_each_problem(self):
        console, lines = scripted_console("abc", "-5", "10")
        self.assertEqual(str(console.ask("Amount: ", validate_amount)), "10.00")
        self.assertEqual(len(lines), 2)
        self.assertIn("not a valid amount", lines[0])
        self.assertIn("greater than zero", lines[1])

    def test_answers_are_stripped(self):
        console, _ = scripted_console("   7   ")
        self.assertEqual(str(console.ask("Amount: ", validate_amount)), "7.00")

    def test_typing_cancel_abandons_the_action(self):
        console, _ = scripted_console("CANCEL")
        with self.assertRaises(Cancelled):
            console.ask("Amount: ", validate_amount)

    def test_ask_optional_returns_none_for_blank(self):
        console, _ = scripted_console("")
        self.assertIsNone(console.ask_optional("Amount: ", validate_amount))

    def test_ask_optional_still_validates_non_blank_answers(self):
        console, lines = scripted_console("zero", "5")
        self.assertEqual(str(console.ask_optional("Amount: ", validate_amount)), "5.00")
        self.assertEqual(len(lines), 1)

    def test_choose_accepts_only_listed_options_ignoring_case(self):
        console, lines = scripted_console("sideways", "ASC")
        self.assertEqual(console.choose("Order: ", ("asc", "desc")), "asc")
        self.assertIn("asc, desc", lines[0])

    def test_confirm(self):
        console, lines = scripted_console("maybe", "Y")
        self.assertTrue(console.confirm("Sure?"))
        self.assertEqual(len(lines), 1)
        console, _ = scripted_console("no")
        self.assertFalse(console.confirm("Sure?"))


class MenuTests(unittest.TestCase):
    def test_choosing_an_option_runs_it_and_the_last_number_leaves(self):
        calls = []
        console, lines = scripted_console("1", "2", "1", "3")
        console.run_menu(
            "TEST MENU",
            [("First", lambda: calls.append("first")), ("Second", lambda: calls.append("second"))],
            leave_label="Exit",
        )
        self.assertEqual(calls, ["first", "second", "first"])
        text = "\n".join(lines)
        self.assertIn("1. First", text)
        self.assertIn("2. Second", text)
        self.assertIn("3. Exit", text)

    def test_invalid_choices_are_reported_and_the_menu_continues(self):
        calls = []
        console, lines = scripted_console("9", "abc", "", "0", "-1", "1", "2")
        console.run_menu("M", [("Only", lambda: calls.append("x"))])
        self.assertEqual(calls, ["x"])
        self.assertEqual(sum("Invalid choice" in line for line in lines), 5)

    def test_cancel_inside_an_action_returns_to_the_menu(self):
        def action():
            raise Cancelled

        console, lines = scripted_console("1", "2")
        console.run_menu("M", [("Act", action)])
        self.assertIn("Cancelled.", lines)

    def test_application_errors_become_messages_not_crashes(self):
        def failing():
            raise StorageError("disk full")

        console, lines = scripted_console("1", "2")
        console.run_menu("M", [("Fail", failing)])
        self.assertIn("Error: disk full", lines)

    def test_validation_errors_from_actions_are_shown(self):
        def failing():
            raise ValidationError("bad value")

        console, lines = scripted_console("1", "2")
        console.run_menu("M", [("Fail", failing)])
        self.assertIn("Error: bad value", lines)

    def test_real_bugs_are_not_hidden(self):
        def buggy():
            raise TypeError("a genuine programming error")

        console, _ = scripted_console("1", "2")
        with self.assertRaises(TypeError):
            console.run_menu("M", [("Bug", buggy)])


if __name__ == "__main__":
    unittest.main()