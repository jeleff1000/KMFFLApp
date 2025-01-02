import streamlit as st
import pandas as pd

class CombinedMatchupStatsViewer:
    def __init__(self, filtered_data, matchup_data):
        self.filtered_data = filtered_data
        self.matchup_data = matchup_data

    def display(self, prefix, show_per_game=False):
        # Merge player data with matchup data
        merged_data = pd.merge(self.filtered_data, self.matchup_data, left_on=['owner', 'week', 'season'], right_on=['Manager', 'week', 'year'], how='inner')

        # Add 'started' column
        merged_data['started'] = ~merged_data['fantasy position'].isin(['BN', 'IR'])

        # Convert 'Included in optimal score' to boolean
        merged_data['Included in optimal score'] = merged_data['Included in optimal score'] == 1

        # Aggregate data by player, position, and season
        agg_funcs = {
            'points': 'sum',
            'team_points': 'sum',
            'win': 'sum',
            'started': 'sum',
            'Included in optimal score': 'sum'
        }
        aggregated_data = merged_data.groupby(['player', 'position', 'season']).agg(agg_funcs).reset_index()

        if show_per_game:
            # Calculate the number of unique weeks for each player
            unique_weeks = merged_data.groupby('player')['week'].nunique().reset_index()
            unique_weeks.columns = ['player', 'unique_weeks']

            # Merge the unique weeks with the aggregated data
            aggregated_data = pd.merge(aggregated_data, unique_weeks, on='player', how='left')

            # Divide all the stats by the number of unique weeks
            numeric_columns = ['points', 'team_points']
            for col in numeric_columns:
                aggregated_data[col] = aggregated_data[col] / aggregated_data['unique_weeks']
                aggregated_data[col] = aggregated_data[col].round(2)

            # Drop the unique_weeks column
            aggregated_data = aggregated_data.drop(columns=['unique_weeks'])

        # Format the 'season' column as a string without commas
        aggregated_data['season'] = aggregated_data['season'].astype(str).str.replace(',', '')

        st.dataframe(aggregated_data, hide_index=True)