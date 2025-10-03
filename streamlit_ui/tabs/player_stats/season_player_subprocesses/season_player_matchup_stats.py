import streamlit as st
import pandas as pd

class CombinedMatchupStatsViewer:
    def __init__(self, filtered_data, matchup_data):
        self.filtered_data = filtered_data
        self.matchup_data = matchup_data

    def display(self, prefix):
        # Ensure correct dtypes
        self.filtered_data = self.filtered_data.copy()
        self.matchup_data = self.matchup_data.copy()
        self.filtered_data['season'] = self.filtered_data['season'].astype(int)
        self.matchup_data['year'] = self.matchup_data['year'].astype(int)

        # Merge player data with matchup data
        merged_data = pd.merge(
            self.filtered_data,
            self.matchup_data,
            left_on=['owner', 'week', 'season', 'opponent'],
            right_on=['manager', 'week', 'year', 'opponent'],
            how='inner'
        )

        # Add 'started' column
        merged_data['started'] = ~merged_data['fantasy_position'].isin(['BN', 'IR'])

        # Convert 'optimal_player' to boolean
        if 'optimal_player' in merged_data.columns:
            merged_data['optimal_player'] = merged_data['optimal_player'] == 1

        if 'win' in merged_data.columns:
            merged_data['win'] = merged_data['win'] == 1
            merged_data['is_playoffs_check'] = merged_data['is_playoffs'] == 1

            # Rank players within RB and WR positions based on points
            merged_data['position_rank'] = merged_data.groupby(
                ['manager', 'week', 'year', 'fantasy_position']
            )['points'].rank(ascending=False, method='first').astype(int)

            # Append the rank only for RB and WR positions
            merged_data['fantasy_position'] = merged_data.apply(
                lambda row: f"{row['fantasy_position']}{row['position_rank']}"
                if row['fantasy_position'] in ['RB', 'WR'] else row['fantasy_position'],
                axis=1
            )

            # Define the unique order for fantasy_positions
            unique_position_order = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'WR3', 'TE', 'W/R/T', 'K', 'DEF', 'BN', 'IR']
            merged_data['fantasy_position'] = pd.Categorical(
                merged_data['fantasy_position'], categories=unique_position_order, ordered=True
            )

            # Create display DataFrame
            display_df = merged_data[
                ['player', 'points', 'manager', 'week', 'year', 'fantasy_position', 'opponent', 'team_points',
                 'opponent_points', 'win', 'is_playoffs_check', 'started', 'optimal_player']
            ].copy()
            display_df['year'] = display_df['year'].astype(str)
            display_df['week'] = display_df['week'].astype(int)
            display_df['points'] = display_df['points'].astype(float)

            # Sort by year, week, and points (descending)
            display_df = display_df.sort_values(
                by=['year', 'week', 'points'],
                ascending=[True, True, False]
            ).reset_index(drop=True)

            st.dataframe(display_df, hide_index=True)