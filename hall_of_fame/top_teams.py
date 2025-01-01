import streamlit as st
import pandas as pd
from .top_weeks import TopWeeksViewer

class TopTeamsViewer:
    def __init__(self, df):
        self.df = df

    def display(self):
        st.header("Top Teams")

        # Create tabs
        tab1, tab2 = st.tabs(["Top Seasons", "Top Weeks"])

        with tab1:
            self.display_top_seasons()

        with tab2:
            top_weeks_viewer = TopWeeksViewer(self.df)
            top_weeks_viewer.display()

    def display_top_seasons(self):
        # Create columns for checkboxes
        col1, col2 = st.columns(2)
        with col1:
            regular_season = st.checkbox("Regular Season", value=True, key="top_seasons_regular_season")
        with col2:
            playoffs = st.checkbox("Playoffs", value=False, key="top_seasons_playoffs")

        if self.df is not None:
            # Create columns for dropdowns with narrower widths
            col3, col4 = st.columns([1, 1])
            with col3:
                years = ["All Years"] + sorted(self.df['year'].unique().tolist())
                selected_year = st.selectbox("Select Year", years, index=0, key="top_seasons_year")
            with col4:
                managers = ["All Managers"] + sorted(self.df['Manager'].unique().tolist())
                selected_manager = st.selectbox("Select Manager", managers, index=0, key="top_seasons_manager")

            # Filter data based on checkboxes
            if regular_season and playoffs:
                filtered_df = self.df[(self.df['is_consolation'] == 0)]
            elif regular_season:
                filtered_df = self.df[(self.df['is_playoffs'] == 0) & (self.df['is_consolation'] == 0)]
            elif playoffs:
                filtered_df = self.df[(self.df['is_playoffs'] == 1) & (self.df['is_consolation'] == 0)]
            else:
                filtered_df = pd.DataFrame()  # No data to display

            # Filter data based on selected year and Manager
            if selected_year != "All Years":
                filtered_df = filtered_df[filtered_df['year'] == selected_year]
            if selected_manager != "All Managers":
                filtered_df = filtered_df[filtered_df['Manager'] == selected_manager]

            if not filtered_df.empty:
                # Calculate top ManagerYear values with top team_points per week and sum of wins and losses
                filtered_df['ManagerYear'] = filtered_df['Manager'] + ' ' + filtered_df['year'].astype(str)
                top_teams_df = filtered_df.groupby(['Manager', 'year']).agg(
                    total_points=('team_points', 'sum'),
                    total_wins=('win', 'sum'),
                    total_losses=('loss', 'sum'),
                    weeks=('week', 'nunique')
                ).reset_index()

                # Calculate PPG and round to two decimals
                top_teams_df['PPG'] = (top_teams_df['total_points'] / top_teams_df['weeks']).round(2)

                # Ensure year column does not have commas
                top_teams_df['year'] = top_teams_df['year'].astype(str)

                # Add champion column based on the Champion column in the data source
                top_teams_df['ManagerYear'] = top_teams_df['Manager'] + ' ' + top_teams_df['year'].astype(str)
                top_teams_df['champion'] = top_teams_df['ManagerYear'].map(
                    lambda my: filtered_df[filtered_df['ManagerYear'] == my]['Champion'].max() == 1
                )

                # Sort by total_points and display
                top_teams_df = top_teams_df.sort_values(by='total_points', ascending=False)
                st.dataframe(top_teams_df[['Manager', 'year', 'total_points', 'total_wins', 'total_losses', 'PPG', 'champion']], hide_index=True)
            else:
                st.write("No data available for the selected filters")
        else:
            st.write("No data available")