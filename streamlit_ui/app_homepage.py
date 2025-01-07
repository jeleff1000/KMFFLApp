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
from tabs.draft_data.draft_data_overview import display_draft_data_overview
from tabs.injury_data.injury_overview import display_injury_overview
from tabs.transactions.transactions_adds_drops_trades_overview import AllTransactionsViewer

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
        tab_names = ["Hall of Fame", "Matchups", "Player Data", "Draft History", "Transactions", "Injuries", "Simulations", "Keeper", "Downloads"]
        tabs = st.tabs(tab_names)

        # Display the content based on the selected tab
        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                if tab_name == "Hall of Fame":
                    hall_of_fame_viewer = HallOfFameViewer(df_dict)
                    hall_of_fame_viewer.display()
                elif tab_name == "Matchups":
                    sub_tab_names = ["Weekly", "Seasons", "Career"]
                    sub_tabs = st.tabs(sub_tab_names)
                    for j, sub_tab_name in enumerate(sub_tab_names):
                        with sub_tabs[j]:
                            matchup_data = df_dict.get("Matchup Data")
                            player_data = df_dict.get("Player Data")
                            if matchup_data is not None and player_data is not None:
                                if sub_tab_name == "Weekly":
                                    matchup_data_viewer = WeeklyMatchupDataViewer(matchup_data, player_data)
                                    matchup_data_viewer.display(prefix="weekly_matchup_data")
                                elif sub_tab_name == "Seasons":
                                    matchup_data_viewer = SeasonMatchupOverviewViewer(matchup_data, player_data)
                                    matchup_data_viewer.display(prefix="season_matchup_data")
                                elif sub_tab_name == "Career":
                                    career_matchup_viewer = CareerMatchupOverviewViewer(matchup_data, player_data)
                                    career_matchup_viewer.display(prefix="career_matchup_data")
                            else:
                                st.error(f"{sub_tab_name} Matchup Data or Player Data not found.")
                elif tab_name == "Player Data":
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
                    draft_history = df_dict.get("Draft History")
                    adds_data = df_dict.get("Adds")
                    if keeper_data is not None and draft_history is not None and adds_data is not None:
                        keeper_data_viewer = KeeperDataViewer(keeper_data, draft_history, adds_data)
                        keeper_data_viewer.display()
                    else:
                        st.error("Keeper data not found.")
                elif tab_name == "Downloads":
                    st.header("Download Data as Excel")
                    if st.button("Download"):
                        output_path = os.path.join(os.path.dirname(__file__), 'Sheet 2.0.xlsx')
                        with pd.ExcelWriter(output_path) as writer:
                            for key, df in df_dict.items():
                                df.to_excel(writer, sheet_name=key, index=False)
                        st.success(f"Data has been downloaded to {output_path}")

if __name__ == "__main__":
    main()