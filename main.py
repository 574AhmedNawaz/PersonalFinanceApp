"""Start the Personal Finance application.

Usage:
    python main.py            choose the command-line or graphical version
    python main.py --cli      start the command-line version
    python main.py --gui      start the graphical version
"""

from __future__ import annotations

import argparse
import sys

from cli.cli_interface import CommandLineApp
from finance_core.errors import StorageError
from finance_core.storage import DEFAULT_BUDGET_FILE, DEFAULT_DATA_FILE, DEFAULT_EXPORT_FILE


def run_cli() -> int:
    try:
        app = CommandLineApp(DEFAULT_DATA_FILE, DEFAULT_BUDGET_FILE, DEFAULT_EXPORT_FILE)
    except StorageError as error:
        print(f"The application could not start: {error}")
        return 1
    app.run()
    return 0


def run_gui() -> int:
    try:
        from gui.gui_interface import run_gui as start_gui
    except ModuleNotFoundError as error:
        if (error.name or "").split(".")[0] == "gui":
            print("The graphical version has not been built yet.")
            return 1
        raise
    return start_gui()


def choose_interface() -> str:
    print("Personal Finance Manager")
    print("  1. Command-line version")
    print("  2. Graphical version")
    print("  3. Quit")
    while True:
        choice = input("Choose an option: ").strip()
        if choice == "1":
            return "cli"
        if choice == "2":
            return "gui"
        if choice == "3":
            return "quit"
        print("Please enter 1, 2 or 3.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Personal Finance and Expense Analytics")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--cli", action="store_true", help="start the command-line version")
    group.add_argument("--gui", action="store_true", help="start the graphical version")
    args = parser.parse_args(argv)

    if args.cli:
        interface = "cli"
    elif args.gui:
        interface = "gui"
    else:
        try:
            interface = choose_interface()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

    if interface == "cli":
        return run_cli()
    if interface == "gui":
        return run_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main())