import streamlit as st
import pandas as pd
from .matchups.weekly.weekly_matchup_overview import WeeklyMatchupDataViewer

class EveryonesScheduleViewer(WeeklyMatchupDataViewer):
    def __init__(self, matchup_data_df, player_data_df):
        super().__init__(matchup_data_df, player_data_df)
        self.df = matchup_data_df

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

        # Initialize result dataframe
        result_df = pd.DataFrame(columns=['Manager'] + [updated for updated in opponents.values()])
        result_df['Manager'] = filtered_df['Manager'].unique()

        # Calculate wins and losses for each manager against each opponent
        for original, updated in opponents.items():
            result_df[updated] = "0-0"
            for manager in result_df['Manager']:
                manager_df = filtered_df[filtered_df['Manager'] == manager]
                opponent_df = filtered_df[filtered_df['Manager'] == original]
                wins = 0
                losses = 0
                for week in manager_df['Cumulative Week'].unique():
                    manager_week_df = manager_df[manager_df['Cumulative Week'] == week]
                    opponent_week_df = opponent_df[opponent_df['Cumulative Week'] == week]
                    if not manager_week_df.empty and not opponent_week_df.empty:
                        if manager_week_df['team_points'].values[0] > opponent_week_df['opponent_score'].values[0]:
                            wins += 1
                        else:
                            losses += 1
                result_df.loc[result_df['Manager'] == manager, updated] = f"{wins}-{losses}"

        # Sort the result dataframe by Manager column alphabetically
        result_df = result_df.sort_values(by='Manager').reset_index(drop=True)

        # Highlight the cell when the schedule name and manager name match
        def highlight_matching_cells(val, manager, column):
            color = 'yellow' if manager in column else ''
            font_weight = 'bold' if manager in column else 'normal'
            return f'background-color: {color}; font-weight: {font_weight}'

        styled_df = result_df.style.apply(lambda x: [highlight_matching_cells(v, x['Manager'], col) for col, v in x.items()], axis=1)

        # Display the result with HTML column names
        st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Display the filtered dataframe for debugging
        #st.dataframe(filtered_df)
