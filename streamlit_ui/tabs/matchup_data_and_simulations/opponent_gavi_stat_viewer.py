import streamlit as st
import pandas as pd
from .matchups.weekly_matchup_overview import WeeklyMatchupDataViewer

class OpponentGaviStatViewer(WeeklyMatchupDataViewer):
    def display(self):
        st.subheader("Opponent Gavi Stat Simulation")

        # Add dropdowns for selecting manager and year with left-aligned narrower width
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            managers = ["All"] + sorted(self.df['Manager'].unique().tolist())
            selected_manager = st.selectbox("Select Manager", managers, key="opponent_gavi_stat_manager_dropdown", help="Select the manager for the simulation")
        with col2:
            years = ["All"] + sorted(self.df['year'].astype(int).unique().tolist())
            default_year = max(years[1:])  # Set default to the largest year
            selected_year = st.selectbox("Select Year", years, index=years.index(default_year), key="opponent_gavi_stat_year_dropdown", help="Select the year for the simulation")

        # Add aggregate toggle
        aggregate_toggle = st.toggle("Aggregate All Years", value=False, key="opponent_gavi_stat_aggregate_toggle")

        # Calculate xWins, xLosses, and delta for each Manager and year
        def calculate_xwins_xlosses(df):
            df['xWins'] = df['opponent_teams_beat_this_week'] / 9
            df['xLosses'] = (df['win'] + df['loss']) - df['xWins']
            df['delta'] = df['win'] - df['xWins']
            return df

        self.df = self.df.groupby(['Manager', 'year']).apply(calculate_xwins_xlosses).reset_index(drop=True)

        # Filter data based on selected manager and year
        if selected_manager != "All":
            filtered_df = self.df[self.df['Manager'] == selected_manager]
        else:
            filtered_df = self.df

        if selected_year != "All":
            filtered_df = filtered_df[filtered_df['year'] == int(selected_year)]

        # Exclude games where is_playoffs or is_consolation is 1
        filtered_df = filtered_df[(filtered_df['is_playoffs'] == 0) & (filtered_df['is_consolation'] == 0)]

        # Group by Manager and year, and aggregate the results
        result_df = filtered_df.groupby(['Manager', 'year']).agg({
            'win': 'sum',
            'loss': 'sum',
            'opponent_teams_beat_this_week': 'sum',
            'xWins': 'sum',
            'xLosses': 'sum',
            'delta': 'sum'
        }).reset_index()

        # If aggregate toggle is selected, aggregate the results based on the manager
        if selected_year == "All" and aggregate_toggle:
            result_df = result_df.groupby('Manager').agg({
                'win': 'sum',
                'loss': 'sum',
                'xWins': 'sum',
                'xLosses': 'sum',
                'delta': 'sum'
            }).reset_index()

        # Check if 'opponent_teams_beat_this_week' exists before dropping
        if 'opponent_teams_beat_this_week' in result_df.columns:
            result_df = result_df.drop(columns=['opponent_teams_beat_this_week'])

        # Format the year column as a string without commas
        if not aggregate_toggle:
            result_df['year'] = result_df['year'].astype(str).str.replace(',', '')

        # Set index to Manager and year if not aggregated
        if aggregate_toggle:
            result_df = result_df.set_index('Manager')
        else:
            result_df = result_df.set_index(['Manager', 'year'])

        # Apply color scale and round for display
        styled_df = result_df.style.format({
            'xWins': '{:.2f}',
            'xLosses': '{:.2f}',
            'delta': '{:.2f}'
        }).background_gradient(
            subset=['win', 'xWins', 'delta'], cmap='RdYlGn', axis=0
        ).background_gradient(
            subset=['loss', 'xLosses'], cmap='RdYlGn_r', axis=0
        )

        # Display the result
        st.dataframe(styled_df)