import streamlit as st
import pandas as pd

class TopWeeksViewer:
    def __init__(self, df):
        self.df = df

    def display(self):
        st.header("Top Weeks")

        # Create columns for checkboxes
        col1, col2 = st.columns(2)
        with col1:
            regular_season = st.checkbox("Regular Season", value=True, key="top_weeks_regular_season")
        with col2:
            playoffs = st.checkbox("Playoffs", value=False, key="top_weeks_playoffs")

        if self.df is not None:
            # Create columns for dropdowns with narrower widths
            col3, col4 = st.columns([1, 1])
            with col3:
                years = ["All Years"] + sorted(self.df['year'].unique().tolist())
                selected_year = st.selectbox("Select Year", years, index=0, key="top_weeks_year")
            with col4:
                managers = ["All Managers"] + sorted(self.df['Manager'].unique().tolist())
                selected_manager = st.selectbox("Select Manager", managers, index=0, key="top_weeks_manager")

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
                # Calculate margin
                filtered_df['margin'] = filtered_df['team_points'] - filtered_df['opponent_score']

                # Ensure year column does not have commas
                filtered_df['year'] = filtered_df['year'].astype(str)

                # Add champion column based on the Champion column in the data source
                filtered_df['champion'] = filtered_df['Champion'] == 1

                # Convert win column to boolean
                filtered_df['win'] = filtered_df['win'] == 1

                # Sort by team_points and display
                filtered_df = filtered_df.sort_values(by='team_points', ascending=False)
                st.dataframe(filtered_df[['Manager', 'week', 'year', 'team_points', 'opponent_score', 'margin', 'win', 'champion']])
            else:
                st.write("No data available for the selected filters")
        else:
            st.write("No data available")