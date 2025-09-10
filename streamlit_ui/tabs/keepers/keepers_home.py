import streamlit as st
import pandas as pd

class KeeperDataViewer:
    def __init__(self, keeper_data):
        self.keeper_data = keeper_data

    def display(self):
        df = self.keeper_data.copy()
        df['season'] = df['season'].astype(str)  # Ensure season is a string
        df = df[df['owner'] != 'No Owner']
        df = df[~df['position'].isin(['DEF', 'K'])]
        df['owner'] = df['owner'].astype(str)

        # Filter to only the largest week in each season
        max_week_per_season = df.groupby('season')['week'].transform('max')
        df = df[df['week'] == max_week_per_season]

        owners = ["All"] + sorted(df['owner'].unique().tolist())
        years = ["All"] + sorted(df['season'].unique().tolist())

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            selected_owners = st.multiselect("Select Owner(s)", owners, default=[], key="keepers_owner_multiselect")
        with col2:
            selected_years = st.multiselect("Select Year(s)", years, default=[], key="keepers_year_multiselect")
        with col3:
            st.write("")
            go_button = st.button("Go", key="keepers_go_button")

        if go_button:
            if selected_owners and "All" not in selected_owners:
                df = df[df['owner'].isin(selected_owners)]
            if selected_years and "All" not in selected_years:
                df = df[df['season'].isin(selected_years)]

            columns_to_display = [
                'player', 'kept_next_year', 'kept_this_year', 'keeper_price', 'team', 'owner', 'position', 'season',
                'avg_points_this_year', 'avg_points_next_year', 'avg_$_next_year',
                'cost', 'faab_bid', 'total_points_next_year'
            ]
            df = df[columns_to_display]
            df = df.dropna(how='all', subset=columns_to_display)

            st.dataframe(df, height=600, width=1200, hide_index=True)