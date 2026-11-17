# Testing

## Automated tests

Run from the project folder:

    python -m unittest

Result on the final version: 374 tests, all passing.

The tests cover the shared core logic (validation, transactions, search and
sort, budgets, analytics, storage and CSV export), the command-line
interface (using a scripted fake console) and the graphical interface
(form checking, shared state, widgets, dialogs and each tab). The graphical
tests are skipped automatically on a machine with no display.

## Manual tests

Each check was run by hand on Windows with `python main.py --cli` or
`python main.py --gui`.

| # | Version | What I did | Expected | Result | 
|---|---------|------------|----------|--------|
| 1 | CLI | Add an income of 1500, category Salary | Saved, gets an ID such as T0001 |the Salary income was saved (T0002).| 
| 2 | CLI | Add an expense of 100, category Food | Saved, appears in the list |the Food expense was saved (T0001).| 
| 3 | CLI | Add an expense with amount `abc` | Clear error message, nothing saved |Error shown for non-numeric and blank amount, asked again | 
| 4 | CLI | Add an expense with date `2026-13-45` | Clear error message, nothing saved | Error shown for impossible date, asked again| 
| 5 | CLI | Edit a transaction's amount | New amount shown in the list |the amount changed from 100.00 to 105.00. Edit it back to 100 later if you want your numbers tidy. | 
| 6 | CLI | Delete a transaction and confirm | Removed from the list |Asked for confirmation, then deleted| 
| 7 | CLI | Search by part of a description | Only matching rows shown | Found only the matching transaction| 
| 8 | CLI | Filter by category and by date range | Only matching rows shown |an exact-date search for 2026-11-16 found only the two transactions from that date. | 
| 9 | CLI | Sort by amount, then by date | Order changes correctly | the list sorted by date, descending, correctly.| 
| 10 | CLI | Set a Food budget of 120 for this month | Budget created |Budget created: Travel, 2026-11, limit 200.006 | 
| 11 | CLI | View budget status with 100 spent | Approaching limit (83.33%) |the Food budget showed 83.33%, Approaching limit.| 
| 12 | CLI | View analytics | Income, expenses, net savings, savings rate agree with the list | the analytics figures matched.| 
| 13 | CLI | Export to CSV and open in Excel | File opens, one row per transaction | pass| 
| 14 | CLI | Close and restart the program | All records are still there |he data was still there after restarting. | 
| 15 | GUI | Open with `python main.py --gui` | Window opens with four tabs |the GUI opened with four tabs. | 
| 16 | GUI | Add a transaction with the amount left blank | Error shown under the field, nothing saved | pass | 
| 17 | GUI | Add, then double-click to edit a transaction | Row updates; dashboard and analytics update too | Pass| 
| 18 | GUI | Delete a transaction | Confirmation shown, row removed |pass | 
| 19 | GUI | Filter and sort using the column headings | Rows filtered, arrow shows direction |pass | 
| 20 | GUI | Create a budget and raise spending above it | Row changes colour: approaching, then exceeded |pass | 
| 21 | GUI | File > Export transactions to CSV | File saved and opens in Excel | pass| 
| 22 | GUI | Compare the same figures in CLI and GUI | Totals are identical |pass | 
| 23 | Both | Damage `data/transactions.json` (a copy) and start | Message shown, file not overwritten | pass| 

## Known limitations

- Single user, one data file per kind; no cloud sync.
- Amounts are limited to the validation rules in `finance_core/validation.py`.
- The graphical tests need Tkinter and a display; they are skipped otherwise.