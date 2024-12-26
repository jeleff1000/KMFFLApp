# Player_Data.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt

class PlayerDataViewer:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.load_button = tk.Button(self.frame, text="Load Excel File", command=self.load_excel_file)
        self.load_button.pack(pady=20)

        self.sheet_combobox = ttk.Combobox(self.frame, state="readonly")
        self.sheet_combobox.pack(pady=5)
        self.sheet_combobox.bind("<<ComboboxSelected>>", self.load_sheet_data)

        self.visualize_button = tk.Button(self.frame, text="Visualize Data", command=self.visualize_data)
        self.visualize_button.pack(pady=5)

        self.player_tree = ttk.Treeview(self.frame, style="Treeview")
        self.player_tree.pack(expand=True, fill=tk.BOTH)

    def preload_excel_file(self, file_path):
        try:
            self.df_dict = pd.read_excel(file_path, sheet_name=None)
            self.sheet_combobox['values'] = list(self.df_dict.keys())
            self.sheet_combobox.current(0)
            self.load_sheet_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def load_excel_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.preload_excel_file(file_path)

    def load_sheet_data(self, event=None):
        sheet_name = self.sheet_combobox.get()
        if sheet_name:
            self.df = self.df_dict[sheet_name]
            self.display_player_data(self.df)

    def visualize_data(self):
        if hasattr(self, 'df'):
            if 'points' in self.df.columns:
                top_players = self.df.nlargest(10, 'points')
                plt.figure(figsize=(10, 6))
                plt.bar(top_players['player_display_name'], top_players['points'], color='skyblue')
                plt.xlabel('player_display_name')
                plt.ylabel('Points')
                plt.title('Top 10 Players by Points')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.show()
            else:
                messagebox.showerror("Error", "The 'points' column does not exist in the data")
        else:
            messagebox.showerror("Error", "No data loaded to visualize")

    def display_player_data(self, df):
        self.player_tree.delete(*self.player_tree.get_children())
        self.player_tree["column"] = list(df.columns)
        self.player_tree["show"] = "headings"

        for column in self.player_tree["columns"]:
            self.player_tree.heading(column, text=column)

        for _, row in df.iterrows():
            self.player_tree.insert("", "end", values=list(row))