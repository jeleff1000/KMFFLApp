import streamlit as st
from .matchups.weekly_matchup_overview import WeeklyMatchupDataViewer
from .shuffle_scores_and_schedules.shuffle_scores import calculate_std_dev, tweak_scores, calculate_playoff_seed
from .shuffle_scores_and_schedules.shuffle_schedule import shuffle_schedule
import numpy as np  # Add this import statement

class TweakScoringViewer:
    def __init__(self, df):
        self.df = df

    def display(self):
        if self.df is not None:
            # Dropdown for selecting year
            col1, col2 = st.columns([1, 3])
            with col1:
                years = ["All Years"] + sorted(self.df['year'].unique().tolist())
                default_year = max(self.df['year'].unique().tolist())
                selected_year = st.selectbox("Select Year", years, index=years.index(default_year))

            # Checkboxes for regular season and postseason
            col3, col4 = st.columns([1, 1])
            with col3:
                show_regular_season = st.checkbox("Regular Season", value=True, key="regular_season_checkbox")
            with col4:
                show_postseason = st.checkbox("Postseason", value=False, key="postseason_checkbox")

            # Checkbox for tweak scores
            col5, col6 = st.columns([1, 1])
            with col5:
                tweak_scores_flag = st.checkbox("Tweak Scores", key="tweak_scores_checkbox")
            with col6:
                shuffle_schedule_flag = st.checkbox("Shuffle Schedule", key="shuffle_schedule_checkbox")

            # Simulate button
            if st.button("Simulate"):
                # Filter data based on selections
                filtered_df = self.df.copy()
                if selected_year != "All Years":
                    filtered_df = filtered_df[filtered_df['year'] == selected_year]

                if show_regular_season and show_postseason:
                    filtered_df = filtered_df[
                        ((filtered_df['is_playoffs'] == 0) & (filtered_df['is_consolation'] == 0)) |
                        (filtered_df['is_playoffs'] == 1)
                    ]
                elif show_regular_season:
                    filtered_df = filtered_df[
                        (filtered_df['is_playoffs'] == 0) & (filtered_df['is_consolation'] == 0)
                    ]
                elif show_postseason:
                    filtered_df = filtered_df[filtered_df['is_playoffs'] == 1]

                # Shuffle schedule if the checkbox is checked
                if shuffle_schedule_flag:
                    filtered_df = shuffle_schedule(filtered_df)

                # Ensure tweaked_team_points column is created
                if 'tweaked_team_points' not in filtered_df.columns:
                    filtered_df['tweaked_team_points'] = filtered_df['team_points']

                # Calculate standard deviation and tweak scores if the checkbox is checked
                if tweak_scores_flag:
                    std_dev_df = calculate_std_dev(filtered_df, selected_year, show_regular_season, show_postseason)
                    filtered_df = tweak_scores(filtered_df, std_dev_df)

                # Ensure Sim_Wins and Sim_Losses columns are created
                if 'Sim_Wins' not in filtered_df.columns:
                    filtered_df['Sim_Wins'] = 0
                if 'Sim_Losses' not in filtered_df.columns:
                    filtered_df['Sim_Losses'] = 0

                # Calculate playoff seeds
                filtered_df = calculate_playoff_seed(filtered_df)

                # Ensure Sim_Playoff_Seed column is created
                if 'Sim_Playoff_Seed' not in filtered_df.columns:
                    filtered_df['Sim_Playoff_Seed'] = np.nan

                # Aggregate data at the season-long level
                aggregated_df = filtered_df.groupby(['year', 'Manager']).agg(
                    Points=('team_points', 'sum'),
                    Sim_Points=('tweaked_team_points', 'sum'),
                    Sim_W=('Sim_Wins', 'sum'),
                    Sim_L=('Sim_Losses', 'sum'),
                    Wins=('win', 'sum'),
                    Losses=('loss', 'sum'),
                    Seed=('Final Playoff Seed', 'max'),
                    Sim_Seed=('Sim_Playoff_Seed', 'max')
                ).reset_index()

                # Remove commas from year column
                aggregated_df['year'] = aggregated_df['year'].astype(str)

                # Sort by playoff seed
                aggregated_df = aggregated_df.sort_values(by=['Seed'])

                # Columns to display
                data_columns = [
                    'Manager', 'Seed', 'Wins', 'Losses', 'Points'
                ]

                sim_columns = [
                    'Manager', 'Sim_Seed', 'Sim_W', 'Sim_L', 'Sim_Points'
                ]

                if selected_year == "All Years":
                    data_columns.insert(0, 'year')
                    sim_columns.insert(0, 'year')

                # Sort simulation columns separately
                sim_aggregated_df = aggregated_df.sort_values(by=['Sim_Seed'])

                # Display the tables side by side
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(aggregated_df[data_columns], hide_index=True)
                with col2:
                    st.dataframe(sim_aggregated_df[sim_columns], hide_index=True)
        else:
            st.write("No data available")