# All_Transactions.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

class AllTransactionsViewer:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.transactions_tree = ttk.Treeview(self.frame, columns=("Player", "Team", "Date"), show="headings")
        self.transactions_tree.heading("Player", text="Player")
        self.transactions_tree.heading("Team", text="Team")
        self.transactions_tree.heading("Date", text="Date")
        self.transactions_tree.pack(expand=True, fill=tk.BOTH)

        self.load_button = tk.Button(self.frame, text="Load Transactions Data", command=self.load_data)
        self.load_button.pack(pady=10)

    def load_data(self):
        # Placeholder for loading data logic
        pass