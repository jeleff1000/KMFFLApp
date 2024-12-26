import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt

class MatchupDataViewer:
    def __init__(self, parent, df_dict):
        self.parent = parent
        self.df_dict = df_dict
        self.frame = ttk.Frame(parent)
        self.frame.pack(expand=True, fill=tk.BOTH)

        # Label for Matchup History
        self.matchup_label = tk.Label(self.frame, text="Matchup History")
        self.matchup_label.pack(side=tk.TOP, padx=5, pady=5)

        # Frame for dropdowns
        self.dropdown_frame = ttk.Frame(self.frame)
        self.dropdown_frame.pack(side=tk.TOP, fill=tk.X, padx=1, pady=1)

        # Manager label and listbox
        self.manager_label = tk.Label(self.dropdown_frame, text="Manager(s):")
        self.manager_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.EW)
        self.manager_listbox = tk.Listbox(self.dropdown_frame, selectmode=tk.MULTIPLE, exportselection=0, width=0)
        self.manager_listbox.grid(row=1, column=0, padx=5, pady=5, sticky=tk.EW)

        # Opponent label and listbox
        self.opponent_label = tk.Label(self.dropdown_frame, text="Opponent(s):")
        self.opponent_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.opponent_listbox = tk.Listbox(self.dropdown_frame, selectmode=tk.MULTIPLE, exportselection=0, width=0)
        self.opponent_listbox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        # Year label and listbox
        self.year_label = tk.Label(self.dropdown_frame, text="Year(s):")
        self.year_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.EW)
        self.year_listbox = tk.Listbox(self.dropdown_frame, selectmode=tk.MULTIPLE, exportselection=0, width=0)
        self.year_listbox.grid(row=1, column=2, padx=5, pady=5, sticky=tk.EW)

        # Checkboxes for including regular season and playoffs
        self.include_regular_season_var = tk.BooleanVar(value=True)
        self.include_regular_season_checkbox = tk.Checkbutton(self.dropdown_frame, text="Include Regular Season",
                                                              variable=self.include_regular_season_var)
        self.include_regular_season_checkbox.grid(row=2, column=0, padx=5, pady=5, sticky=tk.EW)

        self.include_playoffs_var = tk.BooleanVar(value=True)
        self.include_playoffs_checkbox = tk.Checkbutton(self.dropdown_frame, text="Include Playoffs",
                                                        variable=self.include_playoffs_var)
        self.include_playoffs_checkbox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        # Buttons for selecting and clearing selections
        self.select_button = tk.Button(self.dropdown_frame, text="Select", command=self.filter_matchup_data)
        self.select_button.grid(row=2, column=2, padx=5, pady=5, sticky=tk.EW)

        self.clear_button = tk.Button(self.dropdown_frame, text="Clear All", command=self.clear_all_selections)
        self.clear_button.grid(row=3, column=1, padx=5, pady=5)

        # Center the entire row
        for i in range(3):
            self.dropdown_frame.grid_rowconfigure(i, weight=1)
        for j in range(4):
            self.dropdown_frame.grid_columnconfigure(j, weight=1)

        # Treeview for displaying matchup data
        self.matchup_tree = ttk.Treeview(self.frame, style="Treeview")
        self.matchup_tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Treeview for displaying totals
        self.totals_tree = ttk.Treeview(self.frame, style="Treeview")
        self.totals_tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

    def populate_matchup_comboboxes(self, df):
        # Populate the comboboxes with unique values from the dataframe
        if 'Manager' in df.columns and 'opponent' in df.columns and 'year' in df.columns:
            managers = sorted(df['Manager'].astype(str).unique())
            opponents = sorted(df['opponent'].astype(str).unique())
            years = sorted(df['year'].astype(str).unique())
            years.insert(0, "All")
            opponents.insert(0, "All")

            self.manager_listbox.delete(0, tk.END)
            self.opponent_listbox.delete(0, tk.END)
            self.year_listbox.delete(0, tk.END)

            for manager in managers:
                self.manager_listbox.insert(tk.END, manager)
            for opponent in opponents:
                self.opponent_listbox.insert(tk.END, opponent)
            for year in years:
                self.year_listbox.insert(tk.END, year)
        else:
            messagebox.showerror("Error", "The 'Manager', 'opponent', or 'year' column does not exist in the 'Matchup Data' sheet")

    def clear_all_selections(self):
        # Clear all selections in the listboxes
        self.manager_listbox.selection_clear(0, tk.END)
        self.opponent_listbox.selection_clear(0, tk.END)
        self.year_listbox.selection_clear(0, tk.END)

    def filter_matchup_data(self):
        # Filter the matchup data based on selected criteria
        selected_managers = [self.manager_listbox.get(i) for i in self.manager_listbox.curselection()]
        selected_opponents = [self.opponent_listbox.get(i) for i in self.opponent_listbox.curselection()]
        selected_years = [self.year_listbox.get(i) for i in self.year_listbox.curselection()]

        if selected_managers and selected_opponents and selected_years:
            df = self.df_dict['Matchup Data']
            filtered_df = df[df['Manager'].isin(selected_managers) & (df['is_consolation'] != 1)]
            if "All" not in selected_years:
                filtered_df = filtered_df[filtered_df['year'].isin([int(year) for year in selected_years])]
            if "All" not in selected_opponents:
                filtered_df = filtered_df[filtered_df['opponent'].isin(selected_opponents)]
            if not self.include_playoffs_var.get():
                filtered_df = filtered_df[filtered_df['is_playoffs'] != 1]
            if not self.include_regular_season_var.get():
                filtered_df = filtered_df[(filtered_df['is_playoffs'] != 0) | (filtered_df['is_consolation'] != 0)]
            columns_to_display = ['win', 'loss', 'week', 'year', 'team_points', 'opponent_score', 'is_playoffs',
                                  'team_projected_points', 'opponent_projected_points']

            # Check if all columns exist in the DataFrame
            existing_columns = [col for col in columns_to_display if col in filtered_df.columns]

            # Round specified columns to 0 digits and convert to integers using .loc
            for col in ['win', 'loss', 'week', 'year', 'is_playoffs']:
                if col in df.columns:
                    df.loc[:, col] = df[col].round(0).astype(int)

            self.display_matchup_data(filtered_df[existing_columns])
        else:
            messagebox.showerror("Error", "Please select a manager, opponent, and year")

    def display_matchup_data(self, df):
        # Display the filtered matchup data in the Treeview
        self.matchup_tree.delete(*self.matchup_tree.get_children())
        self.matchup_tree["column"] = list(df.columns)
        self.matchup_tree["show"] = "headings"

        column_display_names = {
            'win': 'Win',
            'loss': 'Loss',
            'week': 'Week',
            'year': 'Year',
            'team_points': 'Score',
            'opponent_score': 'Opponent Score',
            'is_playoffs': 'Playoffs'
        }

        for column in self.matchup_tree["columns"]:
            display_name = column_display_names.get(column, column)
            self.matchup_tree.heading(column, text=display_name, anchor='center',
                                      command=lambda _col=column: self.sort_matchup_column(_col, False))
            self.matchup_tree.column(column, anchor='center')

        # Format specified columns to remove decimals using .loc
        for col in ['win', 'loss', 'week', 'year', 'is_playoffs']:
            if col in df.columns:
                df.loc[:, col] = df[col].apply(lambda x: f"{int(x)}")

        for _, row in df.iterrows():
            self.matchup_tree.insert("", "end", values=list(row))

        total_wins = df['win'].astype(int).sum() if 'win' in df.columns else 0
        total_losses = df['loss'].astype(int).sum() if 'loss' in df.columns else 0
        avg_team_points = round(df['team_points'].mean(), 2) if 'team_points' in df.columns else 0
        avg_opponent_score = round(df['opponent_score'].mean(), 2) if 'opponent_score' in df.columns else 0

        self.totals_tree.delete(*self.totals_tree.get_children())
        self.totals_tree["column"] = ["Total Wins", "Total Losses", "Average Score", "Average Opponent Score"]
        self.totals_tree["show"] = "headings"

        for column in self.totals_tree["columns"]:
            self.totals_tree.heading(column, text=column, anchor='center')
            self.totals_tree.column(column, anchor='center')

        total_row = [total_wins, total_losses, avg_team_points, avg_opponent_score]
        self.totals_tree.insert("", "end", values=total_row)

    def sort_matchup_column(self, col, reverse):
        # Sort the Treeview column
        l = [(self.matchup_tree.set(k, col), k) for k in self.matchup_tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.matchup_tree.move(k, '', index)

        self.matchup_tree.heading(col, command=lambda: self.sort_matchup_column(col, not reverse))

    def populate_year_combobox(self, combobox):
        # Populate the year combobox with unique years from the dataframe
        if 'Matchup Data' in self.df_dict:
            df = self.df_dict['Matchup Data']
            if 'year' in df.columns:
                years = df['year'].astype(str).unique()
                years = [year.strip("'[]") for year in years if year.isdigit()]
                combobox['values'] = years
            else:
                messagebox.showerror("Error", "The 'year' column does not exist in the 'Matchup Data' sheet")
        else:
            messagebox.showerror("Error", "'Matchup Data' sheet not found")

if __name__ == "__main__":
    root = tk.Tk()
    app = MatchupDataViewer(root, None)
    root.mainloop()