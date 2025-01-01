import streamlit as st
import pandas as pd
from .season_player_subprocesses.season_player_basic_stats import get_basic_stats
from .season_player_subprocesses.season_player_advanced_stats import get_advanced_stats
from .season_player_subprocesses.season_player_matchup_stats import get_matchup_stats

class StreamlitSeasonPlayerDataViewer:
    def __init__(self, player_data):
        self.basic_stats_df = get_basic_stats()
        self.advanced_stats_df = get_advanced_stats(player_data)
        self.matchup_stats_df = get_matchup_stats(player_data)

    def display(self):
        st.title("Season Player Data Viewer")
        tabs = st.tabs(["Basic Stats", "Advanced Stats", "Matchup Stats"])

        with tabs[0]:
            st.header("Basic Stats")
            st.dataframe(self.basic_stats_df)

        with tabs[1]:
            st.header("Advanced Stats")
            st.dataframe(self.advanced_stats_df)

        with tabs[2]:
            st.header("Matchup Stats")
            st.dataframe(self.matchup_stats_df)