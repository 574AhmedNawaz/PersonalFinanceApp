"""Shared helper for the window tests (not a test file itself).

Every test gets its own hidden Tk window. If this computer has no
display or no Tkinter, the window tests are skipped, not failed.
"""

import unittest

try:
    import tkinter as tk
except ImportError:                                  # pragma: no cover
    raise unittest.SkipTest("Tkinter is not installed")

from tests.state_support import StateTestCase


class FakePrompts:
    """Stands in for the message boxes, which would otherwise wait for a click."""

    def __init__(self, confirm_answer=True):
        self.confirm_answer = confirm_answer
        self.confirms = []
        self.errors = []
        self.infos = []

    def confirm(self, title, message):
        self.confirms.append((title, message))
        return self.confirm_answer

    def error(self, title, message):
        self.errors.append((title, message))

    def info(self, title, message):
        self.infos.append((title, message))


class GuiTestCase(StateTestCase):
    def setUp(self):
        super().setUp()
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(f"No display available: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.prompts = FakePrompts()