import streamlit as st
import pandas as pd
from .career_player_subprocesses.career_player_basic_stats import get_basic_stats
from .career_player_subprocesses.career_player_advanced_stats import get_advanced_stats
from .career_player_subprocesses.career_player_matchup_stats import get_matchup_stats

class StreamlitCareerPlayerDataViewer:
    def __init__(self, player_data):
        self.basic_stats_df = get_basic_stats(player_data)
        self.advanced_stats_df = get_advanced_stats(player_data)
        self.matchup_stats_df = get_matchup_stats(player_data)

    def display(self):
        st.title("Career Player Data Viewer")
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