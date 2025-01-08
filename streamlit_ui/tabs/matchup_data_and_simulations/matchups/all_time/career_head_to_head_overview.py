import pandas as pd
import streamlit as st

class CareerHeadToHeadViewer:
    def __init__(self, df):
        self.df = df

    def display(self):
        st.header("Head-to-Head Matchups")
        if self.df is not None:
            required_columns = ['Manager', 'opponent', 'win', 'loss', 'team_points', 'opponent_score', 'margin']
            if all(column in self.df.columns for column in required_columns):
                # Dropdown for selecting viewer type
                viewer_type = st.selectbox("Select Viewer Type", ["Record", "Total Points", "Per Game", "Margin"])

                if viewer_type == "Record":
                    self.display_record()
                elif viewer_type == "Total Points":
                    self.display_total_points()
                elif viewer_type == "Per Game":
                    self.display_per_game()
                elif viewer_type == "Margin":
                    self.display_margin()
            else:
                st.error("Required columns are missing from the data source")
        else:
            st.error("Matchup Data not available")

    def display_record(self):
        pivot_table = self.df.pivot_table(
            index='Manager', columns='opponent', values=['win', 'loss'], aggfunc='sum', fill_value=0
        )
        win_loss_table = pivot_table.apply(lambda x: x['win'].astype(str) + '-' + x['loss'].astype(str), axis=1)
        st.markdown(win_loss_table.to_html(escape=False, index=True, header=True, index_names=False), unsafe_allow_html=True)

    def display_total_points(self):
        pivot_table = self.df.pivot_table(
            index='Manager', columns='opponent', values='team_points', aggfunc='sum', fill_value=0
        )
        total_points_table = pivot_table.round(2)
        st.markdown(total_points_table.to_html(escape=False, index=True, header=True, index_names=False), unsafe_allow_html=True)

    def display_per_game(self):
        pivot_table = self.df.pivot_table(
            index='Manager', columns='opponent', values='team_points', aggfunc='mean', fill_value=0
        )
        per_game_table = pivot_table.round(2)
        st.markdown(per_game_table.to_html(escape=False, index=True, header=True, index_names=False), unsafe_allow_html=True)

    def display_margin(self):
        pivot_table = self.df.pivot_table(
            index='Manager', columns='opponent', values='margin', aggfunc='sum', fill_value=0
        ).round(2)
        st.markdown(pivot_table.to_html(escape=False, index=True, header=True, index_names=False), unsafe_allow_html=True)