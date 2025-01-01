import os
import streamlit as st
import pandas as pd
import pickle
from tabs.matchup_data_and_simulations.matchups.weekly_matchup_overview import WeeklyMatchupDataViewer
from tabs.matchup_data_and_simulations.matchups.season_matchup_overview import SeasonMatchupOverviewViewer
from tabs.matchup_data_and_simulations.matchups.career_matchup_overview import CareerMatchupOverviewViewer
from tabs.keepers.keepers_home import KeeperDataViewer
from tabs.matchup_data_and_simulations.simulation_home import display_simulations_viewer
from tabs.hall_of_fame.hall_of_fame_homepage import HallOfFameViewer
from tabs.player_stats.weekly_player_stats_overview import StreamlitWeeklyPlayerDataViewer
from tabs.player_stats.season_player_stats_overview import StreamlitSeasonPlayerDataViewer
from tabs.player_stats.career_player_stats_overview import StreamlitCareerPlayerDataViewer

# Function to load the pickle file
@st.cache_data
def load_pickle_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            df_dict = pickle.load(f)
        return df_dict
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return None

def main():
    st.title("KMFFL App")

    # Load the pickle file using a relative path
    file_path = os.path.join(os.path.dirname(__file__), 'Sheet 2.0.pkl')
    df_dict = load_pickle_file(file_path)

    if df_dict:
        # Create tabs
        tab_names = ["Hall of Fame", "Matchup Data", "Player Data", "Draft History", "All Transactions", "Injuries", "Simulations", "Keeper"]
        tabs = st.tabs(tab_names)

        # Display the content based on the selected tab
        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                if tab_name == "Hall of Fame":
                    hall_of_fame_viewer = HallOfFameViewer(df_dict)
                    hall_of_fame_viewer.display()
                elif tab_name == "Matchup Data":
                    st.header("Matchup Data")
                    sub_tab_names = ["Weekly", "Seasons", "Career"]
                    sub_tabs = st.tabs(sub_tab_names)
                    for j, sub_tab_name in enumerate(sub_tab_names):
                        with sub_tabs[j]:
                            if sub_tab_name == "Weekly":
                                weekly_matchup_data = df_dict.get("Matchup Data")
                                if weekly_matchup_data is not None:
                                    matchup_data_viewer = WeeklyMatchupDataViewer(weekly_matchup_data)
                                    matchup_data_viewer.display(prefix="weekly_matchup_data")
                                else:
                                    st.error("Weekly Matchup Data not found.")
                            elif sub_tab_name == "Seasons":
                                season_matchup_data = df_dict.get("Matchup Data")
                                if season_matchup_data is not None:
                                    matchup_data_viewer = SeasonMatchupOverviewViewer(season_matchup_data)
                                    matchup_data_viewer.display(prefix="season_matchup_data")
                                else:
                                    st.error("Season Matchup Data not found.")
                            elif sub_tab_name == "Career":
                                career_matchup_data = df_dict.get("Matchup Data")
                                if career_matchup_data is not None:
                                    career_matchup_viewer = CareerMatchupOverviewViewer(career_matchup_data)
                                    career_matchup_viewer.display(prefix="career_matchup_data")
                                else:
                                    st.error("Career Matchup Data not found.")
                elif tab_name == "Player Data":
                    st.header("Player Data")
                    sub_tab_names = ["Weekly", "Seasons", "Career"]
                    sub_tabs = st.tabs(sub_tab_names)
                    for j, sub_tab_name in enumerate(sub_tab_names):
                        with sub_tabs[j]:
                            player_data = df_dict.get("Player Data")
                            if player_data is not None:
                                if sub_tab_name == "Weekly":
                                    player_data_viewer = StreamlitWeeklyPlayerDataViewer(player_data)
                                    player_data_viewer.display()
                                elif sub_tab_name == "Seasons":
                                    player_data_viewer = StreamlitSeasonPlayerDataViewer(player_data)
                                    player_data_viewer.display()
                                elif sub_tab_name == "Career":
                                    player_data_viewer = StreamlitCareerPlayerDataViewer(player_data)
                                    player_data_viewer.display()
                            else:
                                st.error(f"{sub_tab_name} Player Data not found.")
                elif tab_name == "Draft History":
                    st.header("Draft History")
                    draft_history = df_dict.get("Draft History")
                    if draft_history is not None:
                        st.dataframe(draft_history)
                    else:
                        st.error("Draft History not found.")
                elif tab_name == "All Transactions":
                    st.header("All Transactions")
                    sub_tab_names = ["All Transactions", "Adds", "Drops", "Trades"]
                    sub_tabs = st.tabs(sub_tab_names)
                    for j, sub_tab_name in enumerate(sub_tab_names):
                        with sub_tabs[j]:
                            transaction_data = df_dict.get(sub_tab_name)
                            if transaction_data is not None:
                                st.dataframe(transaction_data)
                            else:
                                st.error(f"{sub_tab_name} data not found.")
                elif tab_name == "Injuries":
                    st.header("Injuries")
                    injury_data = df_dict.get("Injury Data")
                    if injury_data is not None:
                        st.dataframe(injury_data)
                    else:
                        st.error("Injury Data not found.")
                elif tab_name == "Simulations":
                    st.header("Simulations")
                    simulation_data = df_dict.get("Matchup Data")
                    if simulation_data is not None:
                        display_simulations_viewer(simulation_data)
                    else:
                        st.error("Simulation data not found.")
                elif tab_name == "Keeper":
                    st.header("Keeper")
                    keeper_data = df_dict.get("Player Data")
                    draft_history = df_dict.get("Draft History")
                    adds_data = df_dict.get("Adds")
                    if keeper_data is not None and draft_history is not None and adds_data is not None:
                        keeper_data_viewer = KeeperDataViewer(keeper_data, draft_history, adds_data)
                        keeper_data_viewer.display()
                    else:
                        st.error("Keeper data not found.")

if __name__ == "__main__":
    main()