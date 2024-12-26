# Sheet_2.0_UI.py
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from tkinter import ttk
import matplotlib.pyplot as plt
import pickle
from UI_Tabs.Adds import AddsViewer
from UI_Tabs.Matchup_Data import MatchupDataViewer
from UI_Tabs.Draft_History import DraftHistoryViewer
from UI_Tabs.Player_Data import PlayerDataViewer
from UI_Tabs.Simulations import SimulationsViewer

class ExcelViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel Data Viewer")
        self.root.geometry("800x600")

        # Configure Treeview style
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25, bordercolor="black", borderwidth=1)
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        self.style.map("Treeview", background=[('selected', 'blue')])
        self.style.configure("Treeview.Heading", bordercolor="black", borderwidth=1, relief="solid")
        self.style.configure("Treeview", bordercolor="black", borderwidth=1, relief="solid")

        # Create a notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        # Initialize tabs
        self.tabs = {}
        for tab_name in ["Matchup Data", "Player Data", "Draft History", "All Transactions", "Adds", "Drops", "Trades", "Simulations"]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_name)
            self.tabs[tab_name] = frame

        # Load Pickle File button
        self.load_button = tk.Button(root, text="Load Pickle File", command=self.load_pickle_file)
        self.load_button.pack(pady=20)

        # Combobox for selecting sheets
        self.sheet_combobox = ttk.Combobox(root, state="readonly")
        self.sheet_combobox.pack(pady=5)
        self.sheet_combobox.bind("<<ComboboxSelected>>", self.load_sheet_data)

        # Visualize Data button
        self.visualize_button = tk.Button(root, text="Visualize Data", command=self.visualize_data)
        self.visualize_button.pack(pady=5)

        # Initialize Matchup Data tab
        self.matchup_data_viewer = MatchupDataViewer(self.tabs["Matchup Data"], None)
        self.matchup_data_viewer.frame.pack(expand=True, fill=tk.BOTH)

        # Initialize Draft History tab
        self.draft_history_viewer = DraftHistoryViewer(self.tabs["Draft History"])
        self.draft_history_viewer.frame.pack(expand=True, fill=tk.BOTH)

        # Initialize Player Data tab
        self.player_data_viewer = PlayerDataViewer(self.tabs["Player Data"])
        self.player_data_viewer.frame.pack(expand=True, fill=tk.BOTH)

        # Initialize Adds tab
        self.adds_viewer = AddsViewer(self.tabs["Adds"])
        self.adds_viewer.frame.pack(expand=True, fill=tk.BOTH)

        # Initialize Simulations tab
        self.simulations_viewer = SimulationsViewer(self.tabs["Simulations"], None)
        self.simulations_viewer.frame.pack(expand=True, fill=tk.BOTH)

        # Pre-load the specified pickle file
        self.preload_pickle_file(r'C:\Users\joeye\OneDrive\Desktop\kmffl\Adin\Scripts\Sheet 2.0\Sheet 2.0\Sheet 2.0.pkl')

    def preload_pickle_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                self.df_dict = pickle.load(f)
            self.sheet_combobox['values'] = list(self.df_dict.keys())
            self.sheet_combobox.current(0)
            self.load_sheet_data()
            self.matchup_data_viewer.df_dict = self.df_dict
            self.matchup_data_viewer.populate_matchup_comboboxes(self.df_dict['Matchup Data'])
            self.simulations_viewer.df_dict = self.df_dict
            self.simulations_viewer.populate_year_combobox(self.simulations_viewer.year_combobox)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def load_pickle_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Pickle files", "*.pkl")])
        if file_path:
            self.preload_pickle_file(file_path)

    def load_sheet_data(self, event=None):
        sheet_name = self.sheet_combobox.get()
        if sheet_name:
            self.df = self.df_dict[sheet_name]
            if sheet_name == "Draft History":
                self.draft_history_viewer.load_draft_data(self.df)
            elif sheet_name == "Player Data":
                self.player_data_viewer.display_player_data(self.df)

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

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelViewer(root)
    root.mainloop()