# Trades.py
import tkinter as tk
from tkinter import ttk

class TradesViewer:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.trades_tree = ttk.Treeview(self.frame, columns=("Player", "Team", "Date"), show="headings")
        self.trades_tree.heading("Player", text="Player")
        self.trades_tree.heading("Team", text="Team")
        self.trades_tree.heading("Date", text="Date")
        self.trades_tree.pack(expand=True, fill=tk.BOTH)

        self.load_button = tk.Button(self.frame, text="Load Trades Data", command=self.load_data)
        self.load_button.pack(pady=10)

    def load_data(self):
        # Placeholder for loading data logic
        pass