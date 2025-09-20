import streamlit as st
from .gavi_stat_viewer import GaviStatViewer
from .opponent_gavi_stat_viewer import OpponentGaviStatViewer
from .everyones_schedule_viewer import EveryonesScheduleViewer
from .vs_one_opponent_viewer import VsOneOpponentViewer
from .tweak_scoring_viewer import TweakScoringViewer
from .playoff_odds import PlayoffOddsViewer
from .expected_record_viewer import display_expected_record_and_seed  # updated import

class SimulationDataViewer:
    def __init__(self, matchup_data_df, player_data_df):
        self.matchup_data_df = matchup_data_df
        self.player_data_df = player_data_df

    def display(self):
        if self.matchup_data_df is None:
            st.write("")
            return

        what_if_tab, predictive_tab = st.tabs(["What-Ifs", "Predictive"])

        with what_if_tab:
            what_if_options = [
                "",
                "Gavi Stat",
                "Opponent Gavi Stat",
                "Everyone's Schedule",
                "Vs. One Opponent",
                "Expected Record + Seed",
                "Tweak Scoring",
            ]
            what_if_choice = st.selectbox(
                "Select What-If",
                what_if_options,
                key="what_if_simulation_type"
            )

            if what_if_choice == "Gavi Stat":
                GaviStatViewer(self.matchup_data_df, self.player_data_df).display()
            elif what_if_choice == "Opponent Gavi Stat":
                OpponentGaviStatViewer(self.matchup_data_df, self.player_data_df).display()
            elif what_if_choice == "Everyone's Schedule":
                EveryonesScheduleViewer(self.matchup_data_df, self.player_data_df).display()
            elif what_if_choice == "Vs. One Opponent":
                VsOneOpponentViewer(self.matchup_data_df, self.player_data_df).display()
            elif what_if_choice == "Expected Record + Seed":
                display_expected_record_and_seed(self.matchup_data_df, self.player_data_df)
            elif what_if_choice == "Tweak Scoring":
                TweakScoringViewer(self.matchup_data_df, self.player_data_df).display()

        with predictive_tab:
            predictive_options = ["", "Playoff Odds"]
            predictive_choice = st.selectbox(
                "Select Predictive",
                predictive_options,
                key="predictive_simulation_type"
            )

            if predictive_choice == "Playoff Odds":
                PlayoffOddsViewer(self.matchup_data_df).display()

def display_simulations_viewer(matchup_data_df, player_data_df):
    SimulationDataViewer(matchup_data_df, player_data_df).display()