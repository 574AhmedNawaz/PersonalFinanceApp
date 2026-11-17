import csv
import unittest
from unittest import mock

from tests.gui_support import GuiTestCase, tk

from gui.gui_interface import FinanceApp, run_gui


class MainWindowTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.target = self.folder / "export.csv"
        self.chosen = [str(self.target)]
        self.app = FinanceApp(self.root, self.state, self.prompts, save_path_chooser=lambda: self.chosen[0])

    def test_window_has_the_four_tabs(self):
        names = [self.app.notebook.tab(tab, "text") for tab in self.app.notebook.tabs()]
        self.assertEqual(names, ["Dashboard", "Transactions", "Budgets", "Analytics"])
        self.assertEqual(self.root.title(), "Personal Finance Manager")

    def test_a_change_on_one_screen_updates_all_the_others_and_the_status_line(self):
        self.add("expense", "40", "Food", "Shopping", "2026-11-12")
        self.assertEqual(self.app.dashboard.expense_card.text, "40.00")
        self.assertEqual(self.app.transactions_view.table.row_count, 1)
        self.assertEqual(self.app.analytics_view.figures["Total expenses"].cget("text"), "40.00")
        self.assertTrue(self.app.status.cget("text").startswith("Saved at"))

    def test_a_new_budget_appears_on_the_budgets_and_dashboard_tabs(self):
        self.add("expense", "90", "Food", "Shopping", "2026-11-12")
        self.state.create_budget("Food", "2026-11", "100")
        self.assertEqual(self.app.budgets_view.table.row_count, 1)
        self.assertEqual(self.app.dashboard.alerts.all_values()[0][3], "Approaching limit")

    def test_export_writes_a_csv_file_and_tells_the_user(self):
        self.add("income", "100", "Gift", "Present", "2026-11-12")
        self.add("expense", "12.50", "Food", "Lunch, with team", "2026-11-13")
        self.app.export_csv()
        with open(self.target, encoding="utf-8-sig", newline="") as file:
            rows = list(csv.reader(file))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[2][4], "Lunch, with team")
        self.assertIn("Exported 2", self.prompts.infos[0][1])
        self.assertIn("Exported 2", self.app.status.cget("text"))

    def test_export_with_nothing_to_export_says_so(self):
        self.app.export_csv()
        self.assertIn("no transactions", self.prompts.infos[0][1])
        self.assertFalse(self.target.exists())

    def test_cancelling_the_save_window_exports_nothing(self):
        self.add("income", "100", "Gift", "Present", "2026-11-12")
        self.chosen[0] = ""
        self.app.export_csv()
        self.assertFalse(self.target.exists())
        self.assertEqual(self.prompts.infos, [])

    def test_exporting_over_the_data_file_is_refused_with_an_error_box(self):
        self.add("income", "100", "Gift", "Present", "2026-11-12")
        before = self.transactions_file.read_text(encoding="utf-8")
        self.chosen[0] = str(self.transactions_file)
        self.app.export_csv()
        self.assertEqual(self.prompts.errors[0][0], "Export failed")
        self.assertIn("holds your saved data", self.prompts.errors[0][1])
        self.assertEqual(self.transactions_file.read_text(encoding="utf-8"), before)

    def test_a_failed_write_shows_an_error_box_not_a_crash(self):
        self.add("income", "100", "Gift", "Present", "2026-11-12")
        blocker = self.folder / "folder.csv"
        blocker.mkdir()
        self.chosen[0] = str(blocker)
        self.app.export_csv()
        self.assertEqual(self.prompts.errors[0][0], "Export failed")
        self.assertIn("Could not save data", self.prompts.errors[0][1])

    def test_about_box(self):
        self.app.show_about()
        self.assertEqual(self.prompts.infos[0][0], "About")


class StartUpTests(GuiTestCase):
    def test_a_corrupted_data_file_stops_start_up_with_a_message_and_leaves_the_file_alone(self):
        self.transactions_file.write_text("{broken", encoding="utf-8")
        with mock.patch("gui.gui_interface.messagebox.showerror") as showerror:
            with mock.patch("builtins.print"):
                code = run_gui(self.transactions_file, self.budgets_file)
        self.assertEqual(code, 1)
        self.assertIn("not valid JSON", showerror.call_args.args[1])
        self.assertEqual(self.transactions_file.read_text(encoding="utf-8"), "{broken")

    def test_start_up_opens_the_window_and_returns_zero_when_it_is_closed(self):
        with mock.patch("gui.gui_interface.tk.Tk", return_value=self.root):
            with mock.patch.object(self.root, "mainloop") as mainloop:
                with mock.patch.object(self.root, "destroy"):      # the test cleans the window up itself
                    code = run_gui(self.transactions_file, self.budgets_file)
        self.assertEqual(code, 0)
        mainloop.assert_called_once_with()

    def test_no_display_gives_a_message_not_a_traceback(self):
        with mock.patch("gui.gui_interface.tk.Tk", side_effect=tk.TclError("no display")):
            with mock.patch("builtins.print") as printed:
                code = run_gui(self.transactions_file, self.budgets_file)
        self.assertEqual(code, 1)
        self.assertIn("could not open a window", printed.call_args.args[0])


if __name__ == "__main__":
    unittest.main()