import os
import streamlit as st
import pandas as pd
import pickle
from tabs.matchup_data_and_simulations.matchups.matchup_overview import display_matchup_overview
from tabs.keepers.keepers_home import KeeperDataViewer
from tabs.matchup_data_and_simulations.simulation_home import display_simulations_viewer
from tabs.player_stats.weekly_player_stats_overview import StreamlitWeeklyPlayerDataViewer
from tabs.player_stats.season_player_stats_overview import StreamlitSeasonPlayerDataViewer
from tabs.player_stats.career_player_stats_overview import StreamlitCareerPlayerDataViewer
from tabs.draft_data.draft_data_overview import display_draft_data_overview
from tabs.injury_data.injury_overview import display_injury_overview
from tabs.transactions.transactions_adds_drops_trades_overview import AllTransactionsViewer
from tabs.team_names.team_names import display_team_names
from tabs.homepage.homepage_overview import display_homepage_overview
from tabs.graphs.graphs_overview import display_graphs_overview

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
    file_path = os.path.join(os.path.dirname(__file__), 'Sheet 2.0.pkl')
    df_dict = load_pickle_file(file_path)

    if df_dict:
        tab_names = [
            "Homepage", "Manager Stats", "Player Stats", "Draft History", "Transactions",
            "Injuries", "Simulations", "Team Names", "Keeper", "Graphs"
        ]
        tabs = st.tabs(tab_names)

        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                if tab_name == "Homepage":
                    display_homepage_overview(df_dict)
                elif tab_name == "Manager Stats":
                    display_matchup_overview(df_dict)
                elif tab_name == "Player Stats":
                    sub_tab_names = ["Weekly", "Season", "Career"]
                    sub_tabs = st.tabs(sub_tab_names)
                    for j, sub_tab_name in enumerate(sub_tab_names):
                        with sub_tabs[j]:
                            player_data = df_dict.get("Player Data")
                            matchup_data = df_dict.get("Matchup Data")
                            if player_data is not None and matchup_data is not None:
                                if sub_tab_name == "Weekly":
                                    player_data_viewer = StreamlitWeeklyPlayerDataViewer(player_data, matchup_data)
                                    player_data_viewer.display()
                                elif sub_tab_name == "Season":
                                    player_data_viewer = StreamlitSeasonPlayerDataViewer(player_data, matchup_data)
                                    player_data_viewer.display()
                                elif sub_tab_name == "Career":
                                    player_data_viewer = StreamlitCareerPlayerDataViewer(player_data, matchup_data)
                                    player_data_viewer.display()
                            else:
                                st.error(f"{sub_tab_name} Player Data or Matchup Data not found.")
                elif tab_name == "Draft History":
                    display_draft_data_overview(df_dict)
                elif tab_name == "Transactions":
                    transaction_data = df_dict.get("All Transactions")
                    player_data = df_dict.get("Player Data")
                    injury_data = df_dict.get("Injury Data")
                    draft_history_data = df_dict.get("Draft History")
                    if transaction_data is not None and player_data is not None and injury_data is not None and draft_history_data is not None:
                        transactions_viewer = AllTransactionsViewer(transaction_data, player_data, injury_data, draft_history_data)
                        transactions_viewer.display()
                    else:
                        st.error("Transaction data not found.")
                elif tab_name == "Injuries":
                    display_injury_overview(df_dict)
                elif tab_name == "Simulations":
                    st.header("Simulations")
                    simulation_data = df_dict.get("Matchup Data")
                    player_data = df_dict.get("Player Data")
                    if simulation_data is not None and player_data is not None:
                        display_simulations_viewer(simulation_data, player_data)
                    else:
                        st.error("Simulation data not found.")
                elif tab_name == "Keeper":
                    st.header("Keeper")
                    keeper_data = df_dict.get("Player Data")
                    if keeper_data is not None:
                        keeper_data_viewer = KeeperDataViewer(keeper_data)
                        keeper_data_viewer.display()
                    else:
                        st.error("Keeper data not found.")
                elif tab_name == "Team Names":
                    matchup_data = df_dict.get("Matchup Data")
                    display_team_names(matchup_data)
                elif tab_name == "Graphs":
                    display_graphs_overview(df_dict)

if __name__ == "__main__":
    main()