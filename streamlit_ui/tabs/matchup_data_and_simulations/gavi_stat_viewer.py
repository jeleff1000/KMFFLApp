import streamlit as st
import pandas as pd
from .matchups.weekly_matchup_overview import WeeklyMatchupDataViewer

class GaviStatViewer(WeeklyMatchupDataViewer):
    def display(self):
        st.subheader("Gavi Stat Simulation")

        # Add dropdown for selecting year with left-aligned narrower width
        col1, col2 = st.columns([1, 3])
        with col1:
            years = ["All"] + sorted(self.df['year'].astype(int).unique().tolist())
            default_year = max(years[1:])  # Set default to the largest year
            selected_year = st.selectbox("Select Year", years, index=years.index(default_year), key="gavi_stat_year_dropdown", help="Select the year for the simulation")

        # Add checkboxes for including Regular Season, Playoffs, and Consolation in one row
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            include_regular_season = st.checkbox("Include Regular Season", value=True, key="include_regular_season")
        with col2:
            include_playoffs = st.checkbox("Include Playoffs", value=False, key="include_playoffs")
        with col3:
            include_consolation = st.checkbox("Include Consolation", value=False, key="include_consolation")

        # Add Go button
        go_button = st.button("Go", key="gavi_stat_go_button")

        if go_button:
            # Filter data based on selected year
            if selected_year != "All":
                filtered_df = self.df[self.df['year'] == int(selected_year)]
            else:
                filtered_df = self.df

            # Filter data based on checkboxes
            if include_regular_season:
                regular_season_df = filtered_df[(filtered_df['is_playoffs'] == 0) & (filtered_df['is_consolation'] == 0)]
            else:
                regular_season_df = pd.DataFrame()

            if include_playoffs:
                playoffs_df = filtered_df[filtered_df['is_playoffs'] == 1]
            else:
                playoffs_df = pd.DataFrame()

            if include_consolation:
                consolation_df = filtered_df[filtered_df['is_consolation'] == 1]
            else:
                consolation_df = pd.DataFrame()

            filtered_df = pd.concat([regular_season_df, playoffs_df, consolation_df])

            # Group by Manager and aggregate the results
            result_df = filtered_df.groupby('Manager').agg({
                'win': 'sum',
                'loss': 'sum',
                'teams_beat_this_week': 'sum'
            }).reset_index()

            # Calculate xWins, xLosses, and delta
            total_managers = filtered_df['Manager'].nunique()
            result_df['xWins'] = result_df['teams_beat_this_week'] / (total_managers - 1)
            result_df['xLosses'] = result_df['win'] + result_df['loss'] - result_df['xWins']
            result_df['delta'] = result_df['win'] - result_df['xWins']

            # Hide teams_beat_this_week from the viewer
            result_df = result_df.drop(columns=['teams_beat_this_week'])

            # Set index to Manager
            result_df = result_df.set_index('Manager')

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

            # Store the result in session state
            st.session_state['result_df'] = styled_df

        # Display the result if available in session state
        if 'result_df' in st.session_state:
            st.dataframe(st.session_state['result_df'])