import streamlit as st
import pandas as pd
from ..keepers.keepers_home import KeeperDataViewer
from ..matchup_data_and_simulations.simulation_home import display_simulations_viewer
from ..hall_of_fame.top_teams import TopTeamsViewer

class HallOfFameViewer:
    def __init__(self, df_dict):
        self.df_dict = df_dict

    def display_champions(self):
        st.header("Champions")
        matchup_data = self.df_dict.get("Matchup Data")
        if matchup_data is not None:
            required_columns = ['team_points', 'opponent_score', 'Final Wins on Season', 'Final Losses on Season',
                                'team_projected_points', 'opponent_projected_points', 'Personal Season Mean']
            if all(column in matchup_data.columns for column in required_columns):
                champions_df = matchup_data[(matchup_data['championship'] == 1) & (matchup_data['win'] == 1)]
                champions_df['Score'] = champions_df['team_points'].astype(str) + ' - ' + champions_df[
                    'opponent_score'].astype(str)
                champions_df['Record'] = champions_df['Final Wins on Season'].astype(str) + ' - ' + champions_df[
                    'Final Losses on Season'].astype(str)
                champions_df['Projected Score'] = champions_df['team_projected_points'].astype(str) + ' - ' + \
                                                  champions_df['opponent_projected_points'].astype(str)
                champions_df.rename(
                    columns={'Manager': 'Winner', 'opponent': 'Runner-Up', 'Personal Season Mean': 'PPG'}, inplace=True)
                champions_df['year'] = champions_df['year'].astype(str)
                champions_df['PPG'] = champions_df['PPG'].round(2)
                champions_df = champions_df[
                    ['year', 'Winner', 'Runner-Up', 'Record', 'Score', 'Projected Score', 'PPG']].drop_duplicates(
                    subset=['year', 'Winner', 'Runner-Up'])
                champions_df = champions_df.sort_values(by='year', ascending=True)
                champions_df = champions_df.set_index('year')
                st.dataframe(champions_df)
            else:
                st.error("Required columns are missing from the data source")
        else:
            st.error("Matchup Data not available")

    def display(self):
        st.title("Hall of Fame")

        # Dropdown menu for selecting a viewer
        viewer_options = ["Champions", "Matchup Data", "Player Data", "Keeper", "Simulations", "Top Teams"]
        selected_viewer = st.selectbox("Select a Viewer", viewer_options, index=0)

        if selected_viewer == "Champions":
            self.display_champions()
        elif selected_viewer == "Top Teams":
            top_teams_viewer = TopTeamsViewer(self.df_dict.get("Matchup Data"))
            top_teams_viewer.display()
