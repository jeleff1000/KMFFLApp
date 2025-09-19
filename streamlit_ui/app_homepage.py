import os
import sys
import streamlit as st
import pandas as pd

# Ensure the project root (parent of `streamlit_ui`) is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Use absolute imports from the package
from streamlit_ui.tabs.matchup_data_and_simulations.matchups.matchup_overview import display_matchup_overview
from streamlit_ui.tabs.keepers.keepers_home import KeeperDataViewer
from streamlit_ui.tabs.matchup_data_and_simulations.simulation_home import display_simulations_viewer
from streamlit_ui.tabs.player_stats.weekly_player_stats_overview import StreamlitWeeklyPlayerDataViewer
from streamlit_ui.tabs.player_stats.season_player_stats_overview import StreamlitSeasonPlayerDataViewer
from streamlit_ui.tabs.player_stats.career_player_stats_overview import StreamlitCareerPlayerDataViewer
from streamlit_ui.tabs.draft_data.draft_data_overview import display_draft_data_overview
from streamlit_ui.tabs.injury_data.injury_overview import display_injury_overview
from streamlit_ui.tabs.transactions.transactions_adds_drops_trades_overview import AllTransactionsViewer
from streamlit_ui.tabs.team_names.team_names import display_team_names
from streamlit_ui.tabs.homepage.homepage_overview import display_homepage_overview
from streamlit_ui.tabs.graphs.graphs_overview import display_graphs_overview


@st.cache_data(show_spinner=False)
def load_parquet_dfs():
    base_dir = os.path.dirname(__file__)
    files = {
        "Injury Data": "Sheet 2.0_Injury Data.parquet",
        "Schedules": "Sheet 2.0_Schedules.parquet",
        "All Transactions": "Sheet 2.0_All Transactions.parquet",
        "Draft History": "Sheet 2.0_Draft History.parquet",
        "Player Data": "Sheet 2.0_Player Data.parquet",
        "Matchup Data": "Sheet 2.0_Matchup Data.parquet",
    }

    df_dict = {}
    for key, fname in files.items():
        path = os.path.join(base_dir, fname)
        try:
            df_dict[key] = pd.read_parquet(path, engine="pyarrow")
        except FileNotFoundError:
            st.warning(f"Missing file: {path}")
        except Exception as e:
            st.error(f"Failed to read {path}: {e}")
    return df_dict


def main():
    st.title("KMFFL App")
    df_dict = load_parquet_dfs()

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
                                    StreamlitWeeklyPlayerDataViewer(player_data, matchup_data).display()
                                elif sub_tab_name == "Season":
                                    StreamlitSeasonPlayerDataViewer(player_data, matchup_data).display()
                                elif sub_tab_name == "Career":
                                    StreamlitCareerPlayerDataViewer(player_data, matchup_data).display()
                            else:
                                st.error(f"{sub_tab_name} Player Data or Matchup Data not found.")

                elif tab_name == "Draft History":
                    display_draft_data_overview(df_dict)

                elif tab_name == "Transactions":
                    transaction_data = df_dict.get("All Transactions")
                    player_data = df_dict.get("Player Data")
                    injury_data = df_dict.get("Injury Data")
                    draft_history_data = df_dict.get("Draft History")
                    if all(x is not None for x in [transaction_data, player_data, injury_data, draft_history_data]):
                        AllTransactionsViewer(transaction_data, player_data, injury_data, draft_history_data).display()
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
                        KeeperDataViewer(keeper_data).display()
                    else:
                        st.error("Keeper data not found.")

                elif tab_name == "Team Names":
                    matchup_data = df_dict.get("Matchup Data")
                    display_team_names(matchup_data)

                elif tab_name == "Graphs":
                    display_graphs_overview(df_dict)


if __name__ == "__main__":
    main()