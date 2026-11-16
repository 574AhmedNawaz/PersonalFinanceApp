"""Reading input and printing output for the command-line interface.

The Console takes its input and output functions as parameters. The real
program uses input() and print(); the tests pass in scripted versions, so
every menu and prompt can be tested without a person at the keyboard.
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence, TypeVar

from finance_core.errors import FinanceError, ValidationError

T = TypeVar("T")

CANCEL_WORD = "cancel"


class Cancelled(Exception):
    """The user typed 'cancel' to abandon the current action."""


class Console:
    def __init__(
        self,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
    ) -> None:
        self._input_func = input_func
        self._output_func = output_func

    def say(self, text: str = "") -> None:
        self._output_func(text)

    # ----- asking for input -----

    def _read(self, prompt: str) -> str:
        return self._input_func(prompt).strip()

    def ask_text(self, prompt: str) -> str:
        """Read one line. Typing 'cancel' abandons the whole action."""
        text = self._read(prompt)
        if text.lower() == CANCEL_WORD:
            raise Cancelled
        return text

    def ask(self, prompt: str, validator: Callable[[str], T]) -> T:
        """Keep asking until the validator accepts the answer."""
        while True:
            try:
                return validator(self.ask_text(prompt))
            except ValidationError as error:
                self.say(f"  {error}")

    def ask_optional(self, prompt: str, validator: Callable[[str], T]) -> Optional[T]:
        """Like ask(), but an empty answer is allowed and gives None."""
        while True:
            text = self.ask_text(prompt)
            if not text:
                return None
            try:
                return validator(text)
            except ValidationError as error:
                self.say(f"  {error}")

    def choose(self, prompt: str, options: Sequence[str]) -> str:
        """Keep asking until the answer is one of the options."""
        while True:
            answer = self.ask_text(prompt).lower()
            if answer in options:
                return answer
            self.say(f"  Please enter one of: {', '.join(options)}")

    def confirm(self, question: str) -> bool:
        """Ask a yes/no question."""
        while True:
            answer = self.ask_text(f"{question} (y/n): ").lower()
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no"):
                return False
            self.say("  Please answer y or n.")

    # ----- menus -----

    def run_menu(
        self,
        title: str,
        actions: Sequence[tuple[str, Callable[[], None]]],
        leave_label: str = "Back",
    ) -> None:
        """Show a numbered menu until the user picks the last option.

        The options are numbered from 1; the final number is always the
        way out (Back or Exit), so a user can return to the previous
        menu without restarting the program.
        """
        leave_number = str(len(actions) + 1)
        while True:
            self.say()
            self.say(title)
            for number, (label, _) in enumerate(actions, start=1):
                self.say(f"  {number}. {label}")
            self.say(f"  {leave_number}. {leave_label}")

            choice = self._read("Choose an option: ")
            if choice == leave_number:
                return
            if choice.isdecimal() and 1 <= int(choice) <= len(actions):
                self.run_action(actions[int(choice) - 1][1])
            else:
                self.say(f"Invalid choice '{choice}'. Enter a number from 1 to {leave_number}.")

    def run_action(self, action: Callable[[], None]) -> None:
        """Run one menu action, turning expected errors into messages.

        Only the application's own errors (FinanceError) are caught.
        A genuine bug still raises and shows its traceback.
        """
        try:
            action()
        except Cancelled:
            self.say("Cancelled.")
        except FinanceError as error:
            self.say(f"Error: {error}")