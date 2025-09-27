import streamlit as st
import pandas as pd
from .weekly_injury_stats import WeeklyInjuryStatsViewer
from .season_injury_stats import SeasonInjuryStatsViewer
from .career_injury_stats import CareerInjuryStatsViewer

def display_injury_overview(df_dict):
    injury_data = df_dict.get("Injury Data")
    player_data = df_dict.get("Player Data")
    required_columns = {'player', 'week', 'year'}

    if injury_data is not None and player_data is not None:
        # Rename 'full_name' to 'player' in injury_data
        if 'full_name' in injury_data.columns:
            injury_data = injury_data.rename(columns={'full_name': 'player'})
        # Check if required columns exist in both DataFrames
        missing_injury = required_columns - set(injury_data.columns)
        missing_player = required_columns - set(player_data.columns)
        if not missing_injury and not missing_player:
            # Ensure matching dtypes for merge keys
            for col in ['year', 'week']:
                if col in injury_data.columns:
                    injury_data[col] = pd.to_numeric(injury_data[col], errors='coerce')
                if col in player_data.columns:
                    player_data[col] = pd.to_numeric(player_data[col], errors='coerce')
            if 'player' in injury_data.columns and 'player' in player_data.columns:
                injury_data['player'] = injury_data['player'].astype(str)
                player_data['player'] = player_data['player'].astype(str)
            merged_data = pd.merge(injury_data, player_data, on=['player', 'week', 'year'], how='inner')
            injury_stats_viewer = InjuryStatsViewer()
            injury_stats_viewer.display(merged_data)
        else:
            st.error(f"Missing columns: "
                     f"Injury Data: {missing_injury if missing_injury else 'None'}, "
                     f"Player Data: {missing_player if missing_player else 'None'}")
    else:
        st.error("Injury data or Player data not found.")

class InjuryStatsViewer:
    def __init__(self):
        self.weekly_viewer = WeeklyInjuryStatsViewer()
        self.season_viewer = SeasonInjuryStatsViewer()
        self.career_viewer = CareerInjuryStatsViewer()

    def display(self, merged_data):
        # Create tabs
        tab_names = ["Weekly Injury Stats", "Season Injury Stats", "Career Injury Stats"]
        tabs = st.tabs(tab_names)

        # Display content for each tab
        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                if tab_name == "Weekly Injury Stats":
                    self.weekly_viewer.display(merged_data)
                elif tab_name == "Season Injury Stats":
                    self.season_viewer.display(merged_data)
                elif tab_name == "Career Injury Stats":
                    self.career_viewer.display(merged_data)