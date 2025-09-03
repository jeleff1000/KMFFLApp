import streamlit as st
import pandas as pd

class CombinedMatchupStatsViewer:
    def __init__(self, filtered_data, matchup_data):
        self.filtered_data = filtered_data
        self.matchup_data = matchup_data

    def display(self, prefix, show_per_game=False):
        self.filtered_data['season'] = self.filtered_data['season'].astype(int)
        self.matchup_data['year'] = self.matchup_data['year'].astype(int)

        merged_data = pd.merge(
            self.filtered_data, self.matchup_data,
            left_on=['owner', 'week', 'season'],
            right_on=['Manager', 'week', 'year'],
            how='inner'
        )

        merged_data['started'] = ~merged_data['fantasy position'].isin(['BN', 'IR'])
        merged_data['benched'] = merged_data['fantasy position'] == 'BN'
        merged_data['IR'] = merged_data['fantasy position'] == 'IR'
        merged_data['optimal_player'] = merged_data['optimal_player'] == 1
        merged_data['championship_win'] = (merged_data['championship'] == 1) & (merged_data['win'] == 1)
        merged_data['games_played'] = 1  # Each row is a game played

        agg_funcs = {
            'points': 'sum',
            'team_points': 'sum',
            'games_played': 'sum',
            'win': 'sum',
            'loss': 'sum',
            'started': 'sum',
            'benched': 'sum',
            'IR': 'sum',
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

        aggregated_data = aggregated_data.groupby(['player', 'position']).agg({
            'points': 'sum',
            'team_points': 'sum',
            'games_played': 'sum',
            'win': 'sum',
            'loss': 'sum',
            'started': 'sum',
            'benched': 'sum',
            'IR': 'sum',
            'optimal_player': 'sum',
            'quarterfinal': 'sum',
            'semifinal': 'sum',
            'championship': 'sum',
            'Champion': 'sum',
            'is_playoffs': 'sum',
            'championship_win': 'sum',
            'Manager': lambda x: ', '.join(x.unique())
        }).reset_index()

        unique_manager_count = merged_data.groupby(['player', 'position'])['Manager'].nunique().reset_index()
        unique_manager_count.rename(columns={'Manager': 'unique_manager_count'}, inplace=True)
        aggregated_data = pd.merge(aggregated_data, unique_manager_count, on=['player', 'position'], how='left')

        if show_per_game:
            merged_data['week_season'] = merged_data['week'].astype(str) + merged_data['season'].astype(str)
            unique_week_seasons = merged_data.groupby('player')['week_season'].nunique().reset_index()
            unique_week_seasons.columns = ['player', 'unique_week_seasons']
            unique_years = merged_data.groupby('player')['year'].nunique().reset_index()
            unique_years.columns = ['player', 'unique_years']
            aggregated_data = pd.merge(aggregated_data, unique_week_seasons, on='player', how='left')
            aggregated_data = pd.merge(aggregated_data, unique_years, on='player', how='left')
            week_season_columns = ['points', 'team_points', 'games_played', 'win', 'loss', 'started', 'benched', 'IR', 'optimal_player']
            for col in week_season_columns:
                aggregated_data[col] = aggregated_data[col] / aggregated_data['unique_week_seasons']
                aggregated_data[col] = aggregated_data[col].round(2)
            year_columns = ['quarterfinal', 'semifinal', 'championship', 'Champion', 'is_playoffs', 'championship_win']
            for col in year_columns:
                aggregated_data[col] = aggregated_data[col] / aggregated_data['unique_years']
                aggregated_data[col] = aggregated_data[col].round(2)
            aggregated_data = aggregated_data.drop(columns=['unique_week_seasons', 'unique_years'])

        aggregated_data['quarterfinal_check'] = aggregated_data['quarterfinal']
        aggregated_data['semifinal_check'] = aggregated_data['semifinal']
        aggregated_data['championship_check'] = aggregated_data['championship']
        aggregated_data['Team_Made_Playoffs'] = aggregated_data['is_playoffs']

        display_df = aggregated_data[
            ['player', 'position', 'points', 'team_points', 'games_played', 'win', 'loss', 'started', 'benched', 'IR', 'optimal_player',
             'Team_Made_Playoffs', 'quarterfinal_check', 'semifinal_check', 'championship_check', 'championship_win', 'unique_manager_count']
        ]
        st.dataframe(display_df, hide_index=True)