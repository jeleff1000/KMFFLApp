import streamlit as st
import pandas as pd

class KeeperDataViewer:
    def __init__(self, keeper_data):
        self.keeper_data = keeper_data

    def display(self):
        df = self.keeper_data.copy()
        df['year'] = df['year'].astype(str)  # Ensure year is a string
        df = df[df['manager'] != 'No manager']
        df = df[~df['yahoo_position'].isin(['DEF', 'K'])]
        df['manager'] = df['manager'].astype(str)

        # Filter to only the largest week in each year
        max_week_per_year = df.groupby('year')['week'].transform('max')
        df = df[df['week'] == max_week_per_year]

        managers = ["All"] + sorted(df['manager'].unique().tolist())
        years = ["All"] + sorted(df['year'].unique().tolist())

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            selected_managers = st.multiselect("Select manager(s)", managers, default=[], key="keepers_manager_multiselect")
        with col2:
            selected_years = st.multiselect("Select Year(s)", years, default=[], key="keepers_year_multiselect")
        with col3:
            st.write("")
            go_button = st.button("Go", key="keepers_go_button")

        if go_button:
            if selected_managers and "All" not in selected_managers:
                df = df[df['manager'].isin(selected_managers)]
            if selected_years and "All" not in selected_years:
                df = df[df['year'].isin(selected_years)]

            columns_to_display = [
                'player', 'kept_next_year', 'Is Keeper Status', 'keeper_price', 'team', 'manager', 'yahoo_position', 'year',
                'avg_points_this_year', 'avg_points_next_year', 'avg_$_next_year',
                'cost', 'faab_bid', 'total_points_next_year'
            ]
            df = df[columns_to_display]
            df = df.dropna(how='all', subset=columns_to_display)

            # Convert columns to boolean
            df['kept_next_year'] = df['kept_next_year'].astype(bool)
            df['Is Keeper Status'] = df['Is Keeper Status'].astype(bool)

            st.dataframe(df, height=600, width=1200, hide_index=True)