"""Colours, fonts and ttk styles shared by every screen."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from finance_core.budget_service import APPROACHING_LIMIT, EXCEEDED, FULLY_USED, WITHIN_BUDGET

BACKGROUND = "#f4f6f8"
SURFACE = "#ffffff"
TEXT = "#1f2933"
MUTED = "#52606d"
BORDER = "#d3dae2"
ACCENT = "#1d4ed8"
INCOME = "#15803d"
EXPENSE = "#b91c1c"
BAR = "#3b82f6"

# (background, text) for each budget state. The state's name is always
# written in the table as well, so colour is never the only signal.
STATUS_COLOURS = {
    WITHIN_BUDGET: ("#e3f4e8", "#14532d"),
    APPROACHING_LIMIT: ("#fdf0c4", "#713f12"),
    FULLY_USED: ("#dbe8fd", "#1e3a8a"),
    EXCEEDED: ("#fde2e2", "#7f1d1d"),
}


def apply_theme(root: tk.Misc) -> None:
    """Set one consistent look for the whole window."""
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    base = tkfont.nametofont("TkDefaultFont")
    base.configure(size=10)
    tkfont.nametofont("TkTextFont").configure(size=10)
    tkfont.nametofont("TkHeadingFont").configure(size=10, weight="bold")

    root.configure(background=BACKGROUND)
    style.configure(".", background=BACKGROUND, foreground=TEXT)
    style.configure("TFrame", background=BACKGROUND)
    style.configure("TLabel", background=BACKGROUND, foreground=TEXT)
    style.configure("TLabelframe", background=BACKGROUND, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=BACKGROUND, foreground=MUTED,
                    font=("TkDefaultFont", 10, "bold"))
    style.configure("TNotebook", background=BACKGROUND, bordercolor=BORDER)
    style.configure("TNotebook.Tab", padding=(16, 7), font=("TkDefaultFont", 10, "bold"))
    style.configure("TButton", padding=(10, 5))
    style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff")
    style.map("Accent.TButton", background=[("active", "#1e40af"), ("disabled", BORDER)])

    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Error.TLabel", foreground=EXPENSE)
    style.configure("Heading.TLabel", font=("TkDefaultFont", 12, "bold"))
    style.configure("Card.TFrame", background=SURFACE, bordercolor=BORDER, relief="solid", borderwidth=1)
    style.configure("CardTitle.TLabel", background=SURFACE, foreground=MUTED)
    style.configure("CardValue.TLabel", background=SURFACE, font=("TkDefaultFont", 18, "bold"))
    style.configure("Status.TLabel", background=BORDER, foreground=TEXT, padding=(10, 4))

    style.configure("Treeview", rowheight=26, background=SURFACE, fieldbackground=SURFACE,
                    foreground=TEXT, bordercolor=BORDER)
    style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"), padding=(6, 4))
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#ffffff")])