import os
import sys
import streamlit as st
import duckdb
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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

@st.cache_resource
def get_duckdb_conn():
    return duckdb.connect(database=':memory:')

@st.cache_data(show_spinner=False)
def load_duckdb_dfs():
    base_dir = os.path.dirname(__file__)
    files = {
        "Injury Data": "injury.parquet",
        "Schedules": "schedule.parquet",
        "All Transactions": "transactions.parquet",
        "Draft History": "draft.parquet",
        "Player Data": "player.parquet",
        "Matchup Data": "matchup.parquet",
    }
    conn = get_duckdb_conn()
    df_dict = {}
    for key, fname in files.items():
        path = os.path.join(base_dir, fname)
        try:
            df_dict[key] = conn.execute(f"SELECT * FROM '{path}'").df()
        except Exception as e:
            st.warning(f"Failed to read {path}: {e}")
            df_dict[key] = None
    return df_dict

def _normalize_merge_keys(df: pd.DataFrame, *, rename_full_name: bool = False) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df2 = df.copy()
    if rename_full_name and "player" not in df2.columns and "full_name" in df2.columns:
        df2 = df2.rename(columns={"full_name": "player"})
    if "player" in df2.columns:
        df2["player"] = df2["player"].astype(str).str.strip()
    if "week" in df2.columns:
        df2["week"] = pd.to_numeric(df2["week"], errors="coerce")
    if "season" in df2.columns:
        df2["season"] = pd.to_numeric(df2["season"], errors="coerce")
    keys = [c for c in ["player", "week", "season"] if c in df2.columns]
    if set(keys) == {"player", "week", "season"}:
        df2 = df2.dropna(subset=["player", "week", "season"])
        df2["week"] = df2["week"].astype("int64")
        df2["season"] = df2["season"].astype("int64")
    return df2

def _prepare_df_dict_for_injuries(df_dict: dict) -> dict:
    if not df_dict:
        return df_dict
    prepared = dict(df_dict)
    injury_df = df_dict.get("Injury Data")
    player_df = df_dict.get("Player Data")
    prepared["Injury Data"] = _normalize_merge_keys(injury_df, rename_full_name=True) if injury_df is not None else None
    prepared["Player Data"] = _normalize_merge_keys(player_df, rename_full_name=False) if player_df is not None else None
    return prepared

def main():
    st.title("KMFFL App")
    df_dict = load_duckdb_dfs()
    if df_dict:
        tab_names = [
            "Home", "Managers", "Players", "Draft", "Transactions",
            "Simulations", "Extras"
        ]
        tabs = st.tabs(tab_names)
        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                if tab_name == "Home":
                    display_homepage_overview(df_dict)
                elif tab_name == "Managers":
                    display_matchup_overview(df_dict)
                elif tab_name == "Players":
                    sub_tabs = st.tabs(["Stats", "Injuries"])
                    with sub_tabs[0]:
                        stats_tabs = st.tabs(["Weekly", "Season", "Career"])
                        player_data = df_dict.get("Player Data")
                        matchup_data = df_dict.get("Matchup Data")
                        with stats_tabs[0]:
                            if player_data is not None and matchup_data is not None:
                                StreamlitWeeklyPlayerDataViewer(player_data, matchup_data).display()
                            else:
                                st.error("Weekly Player Data or Matchup Data not found.")
                        with stats_tabs[1]:
                            if player_data is not None and matchup_data is not None:
                                StreamlitSeasonPlayerDataViewer(player_data, matchup_data).display()
                            else:
                                st.error("Season Player Data or Matchup Data not found.")
                        with stats_tabs[2]:
                            if player_data is not None and matchup_data is not None:
                                StreamlitCareerPlayerDataViewer(player_data, matchup_data).display()
                            else:
                                st.error("Career Player Data or Matchup Data not found.")
                    with sub_tabs[1]:
                        prepared_dict = _prepare_df_dict_for_injuries(df_dict)
                        display_injury_overview(prepared_dict)
                elif tab_name == "Draft":
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
                elif tab_name == "Simulations":
                    st.header("Simulations")
                    simulation_data = df_dict.get("Matchup Data")
                    player_data = df_dict.get("Player Data")
                    if simulation_data is not None and player_data is not None:
                        display_simulations_viewer(simulation_data, player_data)
                    else:
                        st.error("Simulation data not found.")
                elif tab_name == "Extras":
                    extras_tabs = st.tabs(["Graphs", "Keeper", "Team Names"])
                    with extras_tabs[0]:
                        display_graphs_overview(df_dict)
                    with extras_tabs[1]:
                        st.header("Keeper")
                        keeper_data = df_dict.get("Player Data")
                        if keeper_data is not None:
                            KeeperDataViewer(keeper_data).display()
                        else:
                            st.error("Keeper data not found.")
                    with extras_tabs[2]:
                        matchup_data = df_dict.get("Matchup Data")
                        display_team_names(matchup_data)
    else:
        st.write("No data available")

if __name__ == "__main__":
    main()