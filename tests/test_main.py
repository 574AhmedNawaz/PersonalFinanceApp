import contextlib
import io
import unittest
from unittest import mock

import main


class ChooseInterfaceTests(unittest.TestCase):
    def choose(self, *answers):
        with mock.patch("builtins.input", side_effect=list(answers)):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                return main.choose_interface(), output.getvalue()

    def test_each_option(self):
        self.assertEqual(self.choose("1")[0], "cli")
        self.assertEqual(self.choose("2")[0], "gui")
        self.assertEqual(self.choose("3")[0], "quit")

    def test_invalid_answers_are_asked_again(self):
        choice, output = self.choose("", "9", "cli", " 1 ")
        self.assertEqual(choice, "cli")
        self.assertEqual(output.count("Please enter 1, 2 or 3."), 3)


class MainArgumentTests(unittest.TestCase):
    def test_cli_and_gui_flags_cannot_be_combined(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main.main(["--cli", "--gui"])

    def test_quit_choice_exits_cleanly(self):
        with mock.patch("builtins.input", side_effect=["3"]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main.main([]), 0)

    def test_closed_input_at_the_interface_menu_exits_cleanly(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main.main([]), 0)

    def test_cli_flag_starts_the_command_line_app(self):
        with mock.patch.object(main, "run_cli", return_value=0) as run_cli:
            self.assertEqual(main.main(["--cli"]), 0)
        run_cli.assert_called_once_with()

    def test_choosing_the_command_line_version_from_the_menu_starts_it(self):
        with mock.patch("builtins.input", side_effect=["1"]):
            with mock.patch.object(main, "run_cli", return_value=0) as run_cli:
                with contextlib.redirect_stdout(io.StringIO()):
                    main.main([])
        run_cli.assert_called_once_with()

    def test_a_corrupted_data_file_gives_a_message_and_a_failure_code(self):
        error = main.StorageError("data file is damaged")
        with mock.patch.object(main, "CommandLineApp", side_effect=error):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = main.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("could not start: data file is damaged", output.getvalue())


if __name__ == "__main__":
    unittest.main()