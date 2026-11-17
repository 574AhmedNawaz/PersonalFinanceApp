"""Small reusable widgets: summary card, bar chart, table, period chooser."""

from __future__ import annotations

import tkinter as tk
from decimal import Decimal
from tkinter import ttk
from typing import Callable, Optional, Sequence

from finance_core.display import format_money
from gui import theme
from gui.app_state import ALL_TIME


def shorten(text: str, width: int) -> str:
    """Cut long text so it fits; line breaks become spaces."""
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 3] + "..."


class SummaryCard(ttk.Frame):
    """A boxed title with one big figure underneath."""

    def __init__(self, parent: tk.Misc, title: str) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(14, 10))
        self._title = ttk.Label(self, text=title, style="CardTitle.TLabel")
        self._title.pack(anchor="w")
        self._value = ttk.Label(self, text="-", style="CardValue.TLabel")
        self._value.pack(anchor="w", pady=(4, 0))

    def set(self, text: str, colour: Optional[str] = None) -> None:
        self._value.configure(text=text, foreground=colour or theme.TEXT)

    @property
    def text(self) -> str:
        return str(self._value.cget("text"))


class BarChart(tk.Canvas):
    """Horizontal bars, one per (label, amount), longest first.

    Drawn on a Canvas with the standard library only. Every bar is
    labelled with its amount, so the chart can be read without colour.
    """

    ROW_HEIGHT = 30
    LABEL_WIDTH = 130
    VALUE_WIDTH = 100

    def __init__(self, parent: tk.Misc, empty_text: str = "Nothing to show for this period.") -> None:
        super().__init__(parent, height=self.ROW_HEIGHT * 2, background=theme.SURFACE,
                         highlightthickness=1, highlightbackground=theme.BORDER)
        self._empty_text = empty_text
        self._items: list[tuple[str, Decimal]] = []
        self.bind("<Configure>", lambda event: self._draw())

    def set_data(self, items: Sequence[tuple[str, Decimal]]) -> None:
        self._items = list(items)
        rows = max(len(self._items), 2)
        self.configure(height=rows * self.ROW_HEIGHT + 8)
        self._draw()

    @property
    def item_count(self) -> int:
        return len(self._items)

    def _draw(self) -> None:
        self.delete("all")
        if not self._items:
            self.create_text(12, 20, text=self._empty_text, anchor="w", fill=theme.MUTED)
            return

        width = max(self.winfo_width(), 360)
        bar_area = width - self.LABEL_WIDTH - self.VALUE_WIDTH - 24
        biggest = max(amount for _, amount in self._items)
        for row, (label, amount) in enumerate(self._items):
            top = 6 + row * self.ROW_HEIGHT
            middle = top + self.ROW_HEIGHT // 2
            self.create_text(10, middle, text=shorten(label, 18), anchor="w", fill=theme.TEXT)
            length = 3
            if biggest > 0:
                length = max(3, int(Decimal(bar_area) * amount / biggest))
            left = self.LABEL_WIDTH + 10
            self.create_rectangle(left, top + 5, left + length, top + self.ROW_HEIGHT - 5,
                                  fill=theme.BAR, outline="")
            self.create_text(left + length + 8, middle, text=format_money(amount), anchor="w",
                             fill=theme.TEXT)


class Column:
    """Describes one table column."""

    def __init__(self, key: str, heading: str, width: int, anchor: str = "w", stretch: bool = False):
        self.key = key
        self.heading = heading
        self.width = width
        self.anchor = anchor
        self.stretch = stretch


class DataTable(ttk.Frame):
    """A table with a scroll bar. Rows are (id, values, tag) triples."""

    def __init__(
        self,
        parent: tk.Misc,
        columns: Sequence[Column],
        height: int = 8,
        on_heading_click: Optional[Callable[[str], None]] = None,
        on_double_click: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.columns = list(columns)
        self.tree = ttk.Treeview(self, columns=[c.key for c in self.columns], show="headings",
                                 height=height, selectmode="browse")
        for column in self.columns:
            command = (lambda key=column.key: on_heading_click(key)) if on_heading_click else ""
            self.tree.heading(column.key, text=column.heading, command=command)
            self.tree.column(column.key, width=column.width, anchor=column.anchor,
                             stretch=column.stretch, minwidth=40)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        if on_double_click:
            self.tree.bind("<Double-1>", lambda event: on_double_click())

    def set_rows(self, rows: Sequence[tuple[str, Sequence[str], str]]) -> None:
        self.tree.delete(*self.tree.get_children())
        for row_id, values, tag in rows:
            self.tree.insert("", "end", iid=row_id, values=list(values), tags=(tag,) if tag else ())

    def configure_tag(self, tag: str, **options: str) -> None:
        self.tree.tag_configure(tag, **options)

    def set_heading(self, key: str, text: str) -> None:
        self.tree.heading(key, text=text)

    def selected_id(self) -> Optional[str]:
        selection = self.tree.selection()
        return selection[0] if selection else None

    def select(self, row_id: str) -> None:
        self.tree.selection_set(row_id)

    def row_values(self, row_id: str) -> list[str]:
        return [str(value) for value in self.tree.item(row_id, "values")]

    def all_values(self) -> list[list[str]]:
        return [self.row_values(row_id) for row_id in self.tree.get_children()]

    @property
    def row_count(self) -> int:
        return len(self.tree.get_children())


class PeriodSelector(ttk.Frame):
    """A drop-down list: all time (or all months), or one month."""

    def __init__(self, parent: tk.Misc, on_change: Callable[[], None],
                 all_label: str = ALL_TIME, caption: str = "Period:") -> None:
        super().__init__(parent)
        self._all_label = all_label
        self._on_change = on_change
        ttk.Label(self, text=caption).pack(side="left", padx=(0, 6))
        self.variable = tk.StringVar(value=all_label)
        self.combo = ttk.Combobox(self, textvariable=self.variable, values=[all_label],
                                  state="readonly", width=14)
        self.combo.pack(side="left")
        self.combo.bind("<<ComboboxSelected>>", lambda event: self._on_change())

    def set_months(self, months: Sequence[str]) -> None:
        """Update the choices, keeping the current choice if it still exists."""
        current = self.variable.get()
        choices = [self._all_label, *months]
        self.combo.configure(values=choices)
        if current not in choices:
            self.variable.set(self._all_label)

    def choose(self, value: str) -> None:
        """Pick a value in code (the same as the user choosing it)."""
        self.variable.set(value)
        self._on_change()

    def month(self) -> Optional[str]:
        """The chosen 'YYYY-MM', or None for all time."""
        value = self.variable.get()
        return None if value == self._all_label else value