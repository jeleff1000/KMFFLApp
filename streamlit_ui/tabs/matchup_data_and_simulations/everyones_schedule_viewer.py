import streamlit as st
import pandas as pd
from .matchups.weekly_matchup_overview import WeeklyMatchupDataViewer

class EveryonesScheduleViewer(WeeklyMatchupDataViewer):
    def display(self):
        st.subheader("Everyone's Schedule Simulation")

        # Add dropdown for selecting year with left-aligned narrower width
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        with col1:
            years = ["All"] + sorted(self.df['year'].astype(int).unique().tolist())
            default_year = max(years[1:])  # Set default to the largest year
            selected_year = st.selectbox("Select Year", years, index=years.index(default_year), key="everyones_schedule_year_dropdown")

        # Add checkboxes for including Regular Season and Postseason on the same line
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            include_regular_season = st.checkbox("Include Regular Season", value=True, key="include_regular_season")
        with col2:
            include_postseason = st.checkbox("Include Postseason", value=False, key="include_postseason")

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

        if include_postseason:
            postseason_df = filtered_df[(filtered_df['is_playoffs'] == 1) | (filtered_df['is_consolation'] == 1)]
        else:
            postseason_df = pd.DataFrame()

        filtered_df = pd.concat([regular_season_df, postseason_df])

        # List of opponents with schedule columns
        opponents = {
            "Adin": "Adin's",
            "Daniel": "Daniel's",
            "Eleff": "Eleff's",
            "Gavi": "Gavi's",
            "Jesse": "Jesse's",
            "Kardon": "Kardon's",
            "Leeb": "Leeb's",
            "Newman": "Newman's",
            "Tani": "Tani's",
            "Yaacov": "Yaacov's"
        }

        # Group by Manager and aggregate the results
        result_df = filtered_df.groupby('Manager').sum().reset_index()

        # Combine win and loss columns for each opponent's schedule
        for original, updated in opponents.items():
            result_df[updated] = result_df[f"W vs {original}'s Schedule"].astype(str) + "-" + result_df[f"L vs {original}'s Schedule"].astype(str)
            result_df = result_df.drop(columns=[f"W vs {original}'s Schedule", f"L vs {original}'s Schedule"])

        # Keep only the combined columns
        result_df = result_df[['Manager'] + [updated for updated in opponents.values()]]

        # Highlight the cell when the schedule name and manager name match
        def highlight_matching_cells(val, manager, column):
            color = 'yellow' if manager in column else ''
            font_weight = 'bold' if manager in column else 'normal'
            return f'background-color: {color}; font-weight: {font_weight}'

        styled_df = result_df.style.apply(lambda x: [highlight_matching_cells(v, x['Manager'], col) for col, v in x.items()], axis=1)

        # Display the result with HTML column names
        st.markdown(styled_df.to_html(escape=False), unsafe_allow_html=True)