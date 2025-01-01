import streamlit as st
from .gavi_stat_viewer import GaviStatViewer
from .opponent_gavi_stat_viewer import OpponentGaviStatViewer
from .everyones_schedule_viewer import EveryonesScheduleViewer
from .vs_one_opponent_viewer import VsOneOpponentViewer
from .expected_seed_viewer import ExpectedSeedViewer
from .expected_record_viewer import ExpectedRecordViewer
from .tweak_scoring_viewer import TweakScoringViewer

class SimulationDataViewer:
    def __init__(self, df):
        self.df = df

    def display(self):
        # Add dropdown for selecting simulation type with left-aligned narrower width
        col1, col2 = st.columns([1, 3])
        with col1:
            simulation_type = st.selectbox("Select Simulation Type", [
                "", "Gavi Stat", "Opponent Gavi Stat", "Everyone's Schedule",
                "Vs. One Opponent", "Expected Seed", "Expected Record", "Tweak Scoring"
            ], key="simulation_type_dropdown")

        if simulation_type and self.df is not None:
            viewer = None
            if simulation_type == "Gavi Stat":
                viewer = GaviStatViewer(self.df)
            elif simulation_type == "Opponent Gavi Stat":
                viewer = OpponentGaviStatViewer(self.df)
            elif simulation_type == "Everyone's Schedule":
                viewer = EveryonesScheduleViewer(self.df)
            elif simulation_type == "Vs. One Opponent":
                viewer = VsOneOpponentViewer(self.df)
            elif simulation_type == "Expected Seed":
                viewer = ExpectedSeedViewer(self.df)
            elif simulation_type == "Expected Record":
                viewer = ExpectedRecordViewer(self.df)
            elif simulation_type == "Tweak Scoring":
                viewer = TweakScoringViewer(self.df)

            if viewer:
                viewer.display()
        else:
            st.write("No data available")

def display_simulations_viewer(matchup_data_df):
    # Instantiate the SimulationDataViewer without loading data
    simulation_data_viewer = SimulationDataViewer(matchup_data_df)
    simulation_data_viewer.display()