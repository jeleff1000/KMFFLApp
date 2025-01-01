# Draft_History.py
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

class DraftHistoryViewer:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.draft_tree = ttk.Treeview(self.frame, style="Treeview")
        self.draft_tree.pack(expand=True, fill=tk.BOTH)

    def load_draft_data(self, df):
        self.draft_tree.delete(*self.draft_tree.get_children())
        self.draft_tree["column"] = list(df.columns)
        self.draft_tree["show"] = "headings"

        for column in self.draft_tree["columns"]:
            self.draft_tree.heading(column, text=column, command=lambda _col=column: self.sort_draft_column(_col, False))

        for _, row in df.iterrows():
            self.draft_tree.insert("", "end", values=list(row))

    def sort_draft_column(self, col, reverse):
        l = [(self.draft_tree.set(k, col), k) for k in self.draft_tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.draft_tree.move(k, '', index)

        self.draft_tree.heading(col, command=lambda: self.sort_draft_column(col, not reverse))