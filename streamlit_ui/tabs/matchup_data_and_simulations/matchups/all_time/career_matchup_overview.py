import streamlit as st
import pandas as pd
from .career_optimal_lineups import display_career_optimal_lineup
from .career_head_to_head_overview import CareerHeadToHeadViewer
from .career_team_ratings import CareerTeamRatingsViewer

class CareerMatchupOverviewViewer:
    def __init__(self, df, player_df):
        self.df = df
        self.player_df = player_df

    def filter_data(self, df, regular_season, playoffs, consolation, selected_managers, selected_opponents, selected_years):
        filtered_df = df.copy()
        if regular_season or playoffs or consolation:
            conditions = []
            if regular_season:
                conditions.append((filtered_df['is_playoffs'] == 0) & (filtered_df['is_consolation'] == 0))
            if playoffs:
                conditions.append(filtered_df['is_playoffs'] == 1)
            if consolation:
                conditions.append(filtered_df['is_consolation'] == 1)
            filtered_df = filtered_df[pd.concat(conditions, axis=1).any(axis=1)]
        if selected_managers:
            filtered_df = filtered_df[filtered_df['manager'].isin(selected_managers)]
        if selected_opponents:
            filtered_df = filtered_df[filtered_df['opponent'].isin(selected_opponents)]
        if selected_years:
            filtered_df = filtered_df[filtered_df['year'].isin(selected_years)]
        return filtered_df

    def display(self, prefix=""):
        if self.df is not None:
            # Dropdown filters for manager, opponent, and year
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                managers = sorted(self.df['manager'].unique().tolist())
                selected_managers = st.multiselect("Select Manager(s)", managers, key=f"{prefix}_managers")
            with col2:
                opponents = sorted(self.df['opponent'].unique().tolist())
                selected_opponents = st.multiselect("Select Opponent(s)", opponents, key=f"{prefix}_opponents")
            with col3:
                years = sorted(self.df['year'].astype(int).unique().tolist())
                selected_years = st.multiselect("Select Year(s)", years, key=f"{prefix}_years")

            # Checkboxes for game types
            col4, col5, col6 = st.columns([1, 1, 1])
            with col4:
                regular_season = st.checkbox("Regular Season", value=True, key=f"{prefix}_regular_season_checkbox")
            with col5:
                playoffs = st.checkbox("Playoffs", value=True, key=f"{prefix}_playoffs_checkbox")
            with col6:
                consolation = st.checkbox("Consolation", key=f"{prefix}_consolation_checkbox")

            # Filter the DataFrame
            filtered_df = self.filter_data(self.df, regular_season, playoffs, consolation, selected_managers, selected_opponents, selected_years)

            tab_names = ["Matchup Stats", "Advanced Stats", "Projected Stats", "Optimal Stats", "Team Ratings", "Head-to-Head"]
            tabs = st.tabs(tab_names)

            for i, tab_name in enumerate(tab_names):
                with tabs[i]:
                    if tab_name == "Matchup Stats":
                        from .career_matchup_stats import CareerMatchupStatsViewer
                        viewer = CareerMatchupStatsViewer(filtered_df)
                        viewer.display(prefix=f"{prefix}_{tab_name.lower().replace(' ', '_')}")
                    elif tab_name == "Advanced Stats":
                        from .career_advanced_stats import SeasonAdvancedStatsViewer as CareerAdvancedStatsViewer
                        viewer = CareerAdvancedStatsViewer(filtered_df)
                        viewer.display(prefix=f"{prefix}_{tab_name.lower().replace(' ', '_')}")
                    elif tab_name == "Projected Stats":
                        from .career_projected_stats import SeasonProjectedStatsViewer as CareerProjectedStatsViewer
                        viewer = CareerProjectedStatsViewer(filtered_df)
                        viewer.display(prefix=f"{prefix}_{tab_name.lower().replace(' ', '_')}")
                    elif tab_name == "Optimal Stats":
                        display_career_optimal_lineup(self.player_df, filtered_df)
                    elif tab_name == "Team Ratings":
                        viewer = CareerTeamRatingsViewer(filtered_df)
                        viewer.display(prefix=f"{prefix}_{tab_name.lower().replace(' ', '_')}")
                    elif tab_name == "Head-to-Head":
                        head_to_head_viewer = CareerHeadToHeadViewer(filtered_df)
                        head_to_head_viewer.display()

            st.subheader("Summary Data")
            total_games = len(filtered_df)
            avg_team_points = filtered_df['team_points'].mean()
            avg_opponent_points = filtered_df['opponent_points'].mean()
            st.write(f"Total Games: {total_games} | Avg Team Points: {avg_team_points:.2f} | Avg Opponent Points: {avg_opponent_points:.2f}")
        else:
            st.write("No data available")