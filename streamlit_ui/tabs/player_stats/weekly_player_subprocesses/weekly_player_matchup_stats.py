import streamlit as st
import pandas as pd

class StreamlitWeeklyPlayerDataViewer:
    def __init__(self, player_data, matchup_data):
        self.player_data = player_data
        self.matchup_data = matchup_data

    def display(self, prefix):
        # Merge player data with matchup data
        merged_data = pd.merge(self.filtered_data, self.matchup_data, left_on=['owner', 'week', 'season'], right_on=['Manager', 'week', 'year'], how='inner')

        # Add 'started' column
        merged_data['started'] = ~merged_data['fantasy position'].isin(['BN', 'IR'])

        # Convert 'Included in optimal score' to boolean
        merged_data['Included in optimal score'] = merged_data['Included in optimal score'] == 1

        if 'win' in merged_data.columns:
            merged_data['win'] = merged_data['win'] == 1
            merged_data['is_playoffs_check'] = merged_data['is_playoffs'] == 1
            display_df = merged_data[['player', 'points', 'Manager', 'week', 'year', 'opponent', 'team_points', 'opponent_score', 'win', 'is_playoffs_check', 'started', 'Included in optimal score']]
            display_df['year'] = display_df['year'].astype(str)
            display_df = display_df.sort_values(by=['year', 'week']).reset_index(drop=True)
            st.dataframe(display_df, hide_index=True)
        else:
            st.write("The required column 'win' is not available in the data.")