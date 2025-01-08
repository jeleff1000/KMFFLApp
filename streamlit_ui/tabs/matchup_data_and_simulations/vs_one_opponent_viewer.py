import streamlit as st
import pandas as pd
from .matchups.weekly.weekly_matchup_overview import WeeklyMatchupDataViewer

class VsOneOpponentViewer(WeeklyMatchupDataViewer):
    def __init__(self, matchup_data_df, player_data_df):
        super().__init__(matchup_data_df, player_data_df)
        self.df = matchup_data_df

    def display(self):
        st.subheader("Vs. One Opponent Simulation")

        # Add dropdown for selecting year with left-aligned narrower width
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        with col1:
            years = ["All"] + sorted(self.df['year'].astype(int).unique().tolist())
            default_year = max(years[1:])  # Set default to the largest year
            selected_year = st.selectbox("Select Year", years, index=years.index(default_year), key="vs_one_opponent_year_dropdown")

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

        # List of opponents with original names
        opponents = {
            "Adin": "Adin",
            "Daniel": "Daniel",
            "Eleff": "Eleff",
            "Gavi": "Gavi",
            "Jesse": "Jesse",
            "Kardon": "Kardon",
            "Leeb": "Leeb",
            "Newman": "Newman",
            "Tani": "Tani",
            "Yaacov": "Yaacov"
        }

        # Group by Manager and aggregate the results
        result_df = filtered_df.groupby('Manager').sum().reset_index()

        # Combine win and loss columns for each opponent
        for original, updated in opponents.items():
            result_df[f"Vs<br>{updated}"] = result_df[f"W vs {original}"].astype(str) + "-" + result_df[f"L vs {original}"].astype(str)
            result_df = result_df.drop(columns=[f"W vs {original}", f"L vs {original}"])

        # Keep only the combined "Vs" columns
        result_df = result_df[['Manager'] + [f"Vs<br>{updated}" for updated in opponents.values()]]

        # Display the result with HTML column names and without index
        st.markdown(result_df.to_html(index=False, escape=False), unsafe_allow_html=True)

        # Create a second table showing win-loss for each manager
        win_loss_df = filtered_df.groupby('Manager').agg({'win': 'sum', 'loss': 'sum'}).reset_index()
        win_loss_df['Win-Loss'] = win_loss_df['win'].astype(str) + "-" + win_loss_df['loss'].astype(str)
        win_loss_df = win_loss_df.set_index('Manager')

        # Display the win-loss table
        st.subheader("Win-Loss Record for Each Manager")
        st.dataframe(win_loss_df[['Win-Loss']])