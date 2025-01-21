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

        # Convert 'optimal_player' to boolean
        merged_data['optimal_player'] = merged_data['optimal_player'] == 1

        # Add a new column to check if both championship and win are 1
        merged_data['championship_win'] = (merged_data['championship'] == 1) & (merged_data['win'] == 1)

        # Aggregate data by player, position, and year
        agg_funcs = {
            'points': 'sum',
            'team_points': 'sum',
            'win': 'sum',
            'loss': 'sum',
            'started': 'sum',
            'optimal_player': 'sum',
            'quarterfinal': 'sum',
            'semifinal': 'sum',
            'championship': 'sum',
            'Champion': 'max',
            'is_playoffs': 'max',
            'championship_win': 'sum',
            'Manager': lambda x: ', '.join(x.unique())
        }
        aggregated_data = merged_data.groupby(['player', 'position', 'year']).agg(agg_funcs).reset_index()

        # Sum the max values across all years
        aggregated_data = aggregated_data.groupby(['player', 'position']).agg({
            'points': 'sum',
            'team_points': 'sum',
            'win': 'sum',
            'loss': 'sum',
            'started': 'sum',
            'optimal_player': 'sum',
            'quarterfinal': 'sum',
            'semifinal': 'sum',
            'championship': 'sum',
            'Champion': 'sum',
            'is_playoffs': 'sum',
            'championship_win': 'sum',
            'Manager': lambda x: ', '.join(x.unique())
        }).reset_index()

        # Calculate the count of unique managers
        unique_manager_count = merged_data.groupby(['player', 'position'])['Manager'].nunique().reset_index()
        unique_manager_count.rename(columns={'Manager': 'unique_manager_count'}, inplace=True)

        # Merge the unique manager count back into the aggregated data
        aggregated_data = pd.merge(aggregated_data, unique_manager_count, on=['player', 'position'], how='left')

        if show_per_game:
            # Calculate the number of unique combinations of week and season for each player
            merged_data['week_season'] = merged_data['week'].astype(str) + merged_data['season'].astype(str)
            unique_week_seasons = merged_data.groupby('player')['week_season'].nunique().reset_index()
            unique_week_seasons.columns = ['player', 'unique_week_seasons']

            # Calculate the number of unique years for each player
            unique_years = merged_data.groupby('player')['year'].nunique().reset_index()
            unique_years.columns = ['player', 'unique_years']

            # Merge the unique week_seasons and years with the aggregated data
            aggregated_data = pd.merge(aggregated_data, unique_week_seasons, on='player', how='left')
            aggregated_data = pd.merge(aggregated_data, unique_years, on='player', how='left')

            # Divide specific stats by the number of unique week_seasons
            week_season_columns = ['points', 'team_points', 'win', 'loss', 'started', 'optimal_player']
            for col in week_season_columns:
                aggregated_data[col] = aggregated_data[col] / aggregated_data['unique_week_seasons']
                aggregated_data[col] = aggregated_data[col].round(2)

            # Divide specific stats by the number of unique years
            year_columns = ['quarterfinal', 'semifinal', 'championship', 'Champion', 'is_playoffs', 'championship_win']
            for col in year_columns:
                aggregated_data[col] = aggregated_data[col] / aggregated_data['unique_years']
                aggregated_data[col] = aggregated_data[col].round(2)

            # Drop the unique_week_seasons and unique_years columns
            aggregated_data = aggregated_data.drop(columns=['unique_week_seasons', 'unique_years'])

        # Add checks for playoffs and championship stages as totals
        aggregated_data['quarterfinal_check'] = aggregated_data['quarterfinal']
        aggregated_data['semifinal_check'] = aggregated_data['semifinal']
        aggregated_data['championship_check'] = aggregated_data['championship']
        aggregated_data['Team_Made_Playoffs'] = aggregated_data['is_playoffs']

        # Select and display the required columns
        display_df = aggregated_data[['player', 'position', 'points', 'team_points', 'win', 'loss', 'started', 'optimal_player', 'Team_Made_Playoffs', 'quarterfinal_check', 'semifinal_check', 'championship_check', 'championship_win', 'unique_manager_count']]
        st.dataframe(display_df, hide_index=True)