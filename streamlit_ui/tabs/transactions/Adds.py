# Adds.py
import tkinter as tk
from tkinter import ttk

class AddsViewer:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.tree = ttk.Treeview(self.frame, columns=("Player", "Team", "Date"), show="headings")
        self.tree.heading("Player", text="Player")
        self.tree.heading("Team", text="Team")
        self.tree.heading("Date", text="Date")
        self.tree.pack(expand=True, fill=tk.BOTH)

        self.load_button = tk.Button(self.frame, text="Load Adds Data", command=self.load_data)
        self.load_button.pack(pady=10)

    def load_data(self):
        # Placeholder for loading data logic
        pass