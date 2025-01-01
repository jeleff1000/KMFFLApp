import pandas as pd
import streamlit as st
from .weekly_advanced_stats import WeeklyAdvancedStatsViewer
from .weekly_matchup_stats import WeeklyMatchupStatsViewer
from .weekly_projected_stats import WeeklyProjectedStatsViewer

class WeeklyMatchupDataViewer:
    def __init__(self, df):
        self.df = df

    def filter_data(self, df, regular_season, playoffs, consolation, selected_managers, selected_opponents):
        filtered_df = df[df['Manager'].isin(selected_managers) & df['opponent'].isin(selected_opponents)]

        if regular_season or playoffs or consolation:
            conditions = []
            if regular_season:
                conditions.append((filtered_df['is_playoffs'] == 0) & (filtered_df['is_consolation'] == 0))
            if playoffs:
                conditions.append(filtered_df['is_playoffs'] == 1)
            if consolation:
                conditions.append(filtered_df['is_consolation'] == 1)
            filtered_df = filtered_df[pd.concat(conditions, axis=1).any(axis=1)]

        return filtered_df

    def display(self, prefix=""):
        st.header("Weekly Matchup Data")

        if self.df is not None:
            # Dropdown filters for Manager and opponent
            col1, col2 = st.columns([1, 1])
            with col1:
                managers = ["All"] + sorted(self.df['Manager'].unique().tolist())
                selected_managers = st.multiselect("Select Manager(s)", managers, default=["All"], key=f"{prefix}_managers")
                if "All" in selected_managers:
                    selected_managers = managers[1:]  # Select all managers if "All" is selected

            with col2:
                opponents = ["All"] + sorted(self.df['opponent'].unique().tolist())
                selected_opponents = st.multiselect("Select Opponent(s)", opponents, default=["All"], key=f"{prefix}_opponents")
                if "All" in selected_opponents:
                    selected_opponents = opponents[1:]  # Select all opponents if "All" is selected

            # Checkboxes for game types
            col3, col4, col5 = st.columns([1, 1, 1])
            with col3:
                regular_season = st.checkbox("Regular Season", value=True, key=f"{prefix}_regular_season_checkbox")
            with col4:
                playoffs = st.checkbox("Playoffs", value=True, key=f"{prefix}_playoffs_checkbox")
            with col5:
                consolation = st.checkbox("Consolation", key=f"{prefix}_consolation_checkbox")

            # Filter the DataFrame based on selected managers, opponents, and game types
            filtered_df = self.filter_data(self.df, regular_season, playoffs, consolation, selected_managers, selected_opponents)

            tab_names = ["Matchup Stats", "Advanced Stats", "Projected Stats"]
            tabs = st.tabs(tab_names)

            for i, tab_name in enumerate(tab_names):
                with tabs[i]:
                    if tab_name == "Matchup Stats":
                        viewer = WeeklyMatchupStatsViewer(filtered_df)
                    elif tab_name == "Advanced Stats":
                        viewer = WeeklyAdvancedStatsViewer(filtered_df)
                    elif tab_name == "Projected Stats":
                        viewer = WeeklyProjectedStatsViewer(filtered_df)
                    viewer.display(prefix=f"{prefix}_{tab_name.lower().replace(' ', '_')}")

            st.subheader("Summary Data")
            total_games = len(filtered_df)
            avg_team_points = filtered_df['team_points'].mean()
            avg_opponent_points = filtered_df['opponent_score'].mean()

            st.write(f"Total Games: {total_games} | Avg Team Points: {avg_team_points:.2f} | Avg Opponent Points: {avg_opponent_points:.2f}")
        else:
            st.write("No data available")