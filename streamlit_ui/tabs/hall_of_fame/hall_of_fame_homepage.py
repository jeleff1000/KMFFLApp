import streamlit as st
import pandas as pd

class HallOfFameViewer:
    def __init__(self, df_dict):
        self.df_dict = df_dict

    def display_champions(self):
        st.header("Champions")
        matchup_data = self.df_dict.get("Matchup Data")
        if matchup_data is not None:
            required_columns = [
                'team_points', 'opponent_score', 'final_wins', 'final_losses',
                'team_projected_points', 'opponent_projected_points', 'personal_season_mean',
                'manager', 'opponent', 'year', 'champion', 'championship', 'win'
            ]
            if all(column in matchup_data.columns for column in required_columns):
                champions_df = matchup_data[
                    (matchup_data['championship'] == 1) & (matchup_data['champion'] == 1)
                ].copy()
                champions_df['Score'] = champions_df['team_points'].astype(str) + ' - ' + champions_df['opponent_score'].astype(str)
                champions_df['Record'] = champions_df['final_wins'].astype(str) + ' - ' + champions_df['final_losses'].astype(str)
                champions_df['Projected Score'] = champions_df['team_projected_points'].astype(str) + ' - ' + champions_df['opponent_projected_points'].astype(str)
                champions_df.rename(
                    columns={
                        'manager': 'Winner',
                        'opponent': 'Runner-Up',
                        'personal_season_mean': 'Season-Long PPG'
                    },
                    inplace=True
                )
                champions_df['year'] = champions_df['year'].astype(str)
                champions_df['Season-Long PPG'] = champions_df['Season-Long PPG'].round(2)
                champions_df = champions_df[
                    ['year', 'Winner', 'Runner-Up', 'Record', 'Score', 'Projected Score', 'Season-Long PPG']
                ].drop_duplicates(subset=['year', 'Winner', 'Runner-Up'])
                champions_df = champions_df.sort_values(by='year', ascending=True)
                champions_df = champions_df.set_index('year')
                st.dataframe(champions_df)
            else:
                st.error("Required columns are missing from the data source")
        else:
            st.error("Matchup Data not available")

    def display(self):
        self.display_champions()