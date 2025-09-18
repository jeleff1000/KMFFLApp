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
        col1, col2 = st.columns([1, 3])
        with col1:
            simulation_type = st.selectbox(
                "Select Simulation Type",
                [
                    "",
                    "Playoff Odds",
                    "Gavi Stat",
                    "Opponent Gavi Stat",
                    "Everyone's Schedule",
                    "Vs. One Opponent",
                    "Expected Record + Seed",
                    "Tweak Scoring"
                ],
                key="simulation_type_dropdown"
            )

        if not simulation_type or self.matchup_data_df is None:
            st.write("No data available")
            return

        if simulation_type == "Playoff Odds":
            PlayoffOddsViewer(self.matchup_data_df).display()
        elif simulation_type == "Gavi Stat":
            GaviStatViewer(self.matchup_data_df, self.player_data_df).display()
        elif simulation_type == "Opponent Gavi Stat":
            OpponentGaviStatViewer(self.matchup_data_df, self.player_data_df).display()
        elif simulation_type == "Everyone's Schedule":
            EveryonesScheduleViewer(self.matchup_data_df, self.player_data_df).display()
        elif simulation_type == "Vs. One Opponent":
            VsOneOpponentViewer(self.matchup_data_df, self.player_data_df).display()
        elif simulation_type == "Expected Record + Seed":
            display_expected_record_and_seed(self.matchup_data_df, self.player_data_df)
        elif simulation_type == "Tweak Scoring":
            TweakScoringViewer(self.matchup_data_df, self.player_data_df).display()

def display_simulations_viewer(matchup_data_df, player_data_df):
    SimulationDataViewer(matchup_data_df, player_data_df).display()