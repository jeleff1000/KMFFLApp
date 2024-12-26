# Simulations.py
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

class SimulationsViewer:
    def __init__(self, parent, df_dict):
        self.parent = parent
        self.df_dict = df_dict
        self.frame = ttk.Frame(parent)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.simulation_type_combobox = ttk.Combobox(self.frame, state="readonly")
        self.simulation_type_combobox['values'] = ["Gavi Stat", "Opponent Gavi Stat"]
        self.simulation_type_combobox.pack(pady=5)

        self.year_combobox = ttk.Combobox(self.frame, state="readonly")
        self.year_combobox.pack(pady=5)

        self.calculate_button = tk.Button(self.frame, text="Calculate Simulation", command=self.calculate_simulation)
        self.calculate_button.pack(pady=20)

        self.include_playoffs_var = tk.BooleanVar()
        self.include_playoffs_checkbox = tk.Checkbutton(self.frame, text="Include Playoffs", variable=self.include_playoffs_var)
        self.include_playoffs_checkbox.pack(pady=5)

        self.include_regular_season_var = tk.BooleanVar(value=True)
        self.include_regular_season_checkbox = tk.Checkbutton(self.frame, text="Include Regular Season", variable=self.include_regular_season_var)
        self.include_regular_season_checkbox.pack(pady=5)

        self.gavi_tree = ttk.Treeview(self.frame, style="Treeview")
        self.gavi_tree.pack(expand=True, fill=tk.BOTH)

    def calculate_simulation(self):
        simulation_type = self.simulation_type_combobox.get()
        selected_year = self.year_combobox.get().strip("'")

        if not simulation_type:
            messagebox.showerror("Error", "Please select a simulation type")
            return

        if not selected_year:
            messagebox.showerror("Error", "Please select a year")
            return

        if simulation_type == "Gavi Stat":
            self.calculate_gavi_stat()
        elif simulation_type == "Opponent Gavi Stat":
            self.calculate_gavi_stat(opponent=True)

    def calculate_gavi_stat(self, opponent=False):
        if 'Matchup Data' in self.df_dict:
            df = self.df_dict['Matchup Data']
            if 'year' in df.columns and 'Manager' in df.columns and 'win' in df.columns and 'teams_beat_this_week' in df.columns:
                selected_year = self.year_combobox.get().strip("'")
                if selected_year:
                    if selected_year == "All Years":
                        df_year = df
                    else:
                        df_year = df[df['year'] == int(selected_year)]

                    # Filter out rows where is_consolation is 1
                    df_year = df_year[df_year['is_consolation'] != 1]

                    # Filter out rows where is_playoffs is 1 unless include_playoffs is checked
                    if not self.include_playoffs_var.get():
                        df_year = df_year[df_year['is_playoffs'] != 1]

                    # Fill missing values in teams_beat_this_week with 0
                    df_year['teams_beat_this_week'] = df_year['teams_beat_this_week'].fillna(0)

                    if opponent:
                        gavi_stat_df = df_year.groupby('opponent').agg(
                            win=('win', 'sum'),
                            loss=('win', 'count'),
                            teams_beat_this_week=('teams_beat_this_week', 'sum')
                        ).reset_index()
                        gavi_stat_df.rename(columns={'opponent': 'Manager'}, inplace=True)
                        gavi_stat_df['loss'] = gavi_stat_df['loss'] - gavi_stat_df['win']
                        gavi_stat_df['record'] = gavi_stat_df['loss'].astype(str) + " - " + gavi_stat_df['win'].astype(str)
                        gavi_stat_df['expected_wins'] = (gavi_stat_df['teams_beat_this_week'] / 9).round(2)
                        gavi_stat_df['expected_record'] = (gavi_stat_df['win'] + gavi_stat_df['loss'] - gavi_stat_df['expected_wins']).round(2).astype(str) + " - " + gavi_stat_df['expected_wins'].round(2).astype(str)
                        gavi_stat_df['delta'] = (gavi_stat_df['expected_wins'] - gavi_stat_df['win']).round(2)
                    else:
                        gavi_stat_df = df_year.groupby('Manager').agg(
                            win=('win', 'sum'),
                            loss=('win', 'count'),
                            teams_beat_this_week=('teams_beat_this_week', 'sum')
                        ).reset_index()
                        gavi_stat_df['loss'] = gavi_stat_df['loss'] - gavi_stat_df['win']
                        gavi_stat_df['record'] = gavi_stat_df['win'].astype(str) + " - " + gavi_stat_df['loss'].astype(str)
                        gavi_stat_df['expected_wins'] = (gavi_stat_df['teams_beat_this_week'] / 9).round(2)
                        gavi_stat_df['expected_record'] = gavi_stat_df['expected_wins'].round(2).astype(str) + " - " + (gavi_stat_df['win'] + gavi_stat_df['loss'] - gavi_stat_df['expected_wins']).round(2).astype(str)
                        gavi_stat_df['delta'] = (gavi_stat_df['win'] - gavi_stat_df['expected_wins']).round(2)

                    self.display_gavi_stat(gavi_stat_df)
                else:
                    messagebox.showerror("Error", "Please select a year")
            else:
                messagebox.showerror("Error", "Required columns are missing in the 'Matchup Data' sheet")
        else:
            messagebox.showerror("Error", "'Matchup Data' sheet not found")

    def display_gavi_stat(self, df):
        self.gavi_tree.delete(*self.gavi_tree.get_children())
        self.gavi_tree["column"] = ["Manager", "Real Record", "Expected Record", "Delta"]
        self.gavi_tree["show"] = "headings"

        for column in self.gavi_tree["column"]:
            self.gavi_tree.heading(column, text=column,
                                   command=lambda _col=column: self.sort_gavi_stat_column(_col, False))
            self.gavi_tree.column(column, anchor=tk.CENTER)  # Center the column values

        # Define color gradient tags for delta
        self.gavi_tree.tag_configure('delta_low', background='#FFCCCC')
        self.gavi_tree.tag_configure('delta_medium', background='#FFFF99')
        self.gavi_tree.tag_configure('delta_high', background='#CCFFCC')

        # Define color gradient tags for record
        self.gavi_tree.tag_configure('record_low', background='#CCE5FF')
        self.gavi_tree.tag_configure('record_medium', background='#99CCFF')
        self.gavi_tree.tag_configure('record_high', background='#66B2FF')

        # Define color gradient tags for expected_record
        self.gavi_tree.tag_configure('expected_record_low', background='#E5CCFF')
        self.gavi_tree.tag_configure('expected_record_medium', background='#CC99FF')
        self.gavi_tree.tag_configure('expected_record_high', background='#B266FF')

        for _, row in df.iterrows():
            delta_value = row["delta"]
            win_value = row["win"]
            expected_wins_value = row["expected_wins"]

            if delta_value < 0:
                delta_tag = 'delta_low'
            elif delta_value < 1:
                delta_tag = 'delta_medium'
            else:
                delta_tag = 'delta_high'

            if win_value < 5:
                record_tag = 'record_low'
            elif win_value < 10:
                record_tag = 'record_medium'
            else:
                record_tag = 'record_high'

            if expected_wins_value < 5:
                expected_record_tag = 'expected_record_low'
            elif expected_wins_value < 10:
                expected_record_tag = 'expected_record_medium'
            else:
                expected_record_tag = 'expected_record_high'

            self.gavi_tree.insert("", "end",
                                  values=[row["Manager"], row["record"], row["expected_record"], row["delta"]],
                                  tags=(delta_tag, record_tag, expected_record_tag))

    def sort_gavi_stat_column(self, col, reverse):
        if col == 'Delta':
            l = [(float(self.gavi_tree.set(k, col)), k) for k in self.gavi_tree.get_children('')]
        elif col == 'Real Record':
            l = [(int(self.gavi_tree.set(k, 'Real Record').split(' - ')[0]), k) for k in self.gavi_tree.get_children('')]
        elif col == 'Expected Record':
            l = [(float(self.gavi_tree.set(k, 'Expected Record').split(' - ')[0]), k) for k in self.gavi_tree.get_children('')]
        else:
            l = [(self.gavi_tree.set(k, col), k) for k in self.gavi_tree.get_children('')]

        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.gavi_tree.move(k, '', index)

        self.gavi_tree.heading(col, command=lambda: self.sort_gavi_stat_column(col, not reverse))

    def populate_year_combobox(self, combobox):
        if 'Matchup Data' in self.df_dict:
            df = self.df_dict['Matchup Data']
            if 'year' in df.columns:
                years = df['year'].astype(str).unique()
                years = [year.strip("'[]") for year in years if year.isdigit()]
                years.insert(0, "All Years")
                combobox['values'] = years
            else:
                messagebox.showerror("Error", "The 'year' column does not exist in the 'Matchup Data' sheet")
        else:
            messagebox.showerror("Error", "'Matchup Data' sheet not found")