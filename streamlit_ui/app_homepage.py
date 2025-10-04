import os
import sys
from pathlib import Path
from typing import Dict, Optional, Callable, Any

import duckdb
import streamlit as st

APP_FILE = Path(__file__).resolve()
APP_DIR = APP_FILE.parent

def _resolve_repo_root() -> Path:
    p = APP_DIR
    for _ in range(10):
        if (p / "streamlit_ui").exists():
            return p
        p = p.parent
    return APP_DIR

REPO_ROOT = _resolve_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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

DATA_DIR = Path(os.getenv("KMFFL_DATA_DIR", APP_DIR)).resolve()
FILE_MAP: Dict[str, Path] = {
    "Matchup Data": DATA_DIR / "matchup.parquet",
    "Player Data": DATA_DIR / "player.parquet",
    "Schedules": DATA_DIR / "schedule.parquet",
    "All Transactions": DATA_DIR / "transactions.parquet",
    "Draft History": DATA_DIR / "draft.parquet",
    "Injury Data": DATA_DIR / "injury.parquet",
}

@st.cache_resource
def get_duckdb_connection():
    return duckdb.connect(database=":memory:")

def load_parquet_duckdb(con: duckdb.DuckDBPyConnection, path: Path, table_name: str) -> None:
    safe_path = str(path).replace("'", "''")
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{safe_path}')")

@st.cache_data(show_spinner=False)
def load_all_dfs(file_map: Dict[str, Path], _con: duckdb.DuckDBPyConnection) -> Dict[str, Optional[Any]]:
    tables = {}
    for key, path in file_map.items():
        if not path.exists():
            st.warning(f"{key}: File not found at {path}")
            tables[key] = None
            continue
        try:
            table_name = key.lower().replace(" ", "_")
            load_parquet_duckdb(_con, path, table_name)
            row_count = _con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            st.success(f"{key}: Loaded {row_count:,} rows into DuckDB")
            tables[key] = table_name
        except Exception as e:
            st.error(f"{key}: Failed to load - {type(e).__name__}: {e}")
            tables[key] = None
    return tables

def query_to_df(con: duckdb.DuckDBPyConnection, query: str):
    return con.execute(query).df()

def safe_render(title: str, fn: Callable[..., Any], *args, **kwargs) -> None:
    try:
        fn(*args, **kwargs)
    except Exception as e:
        st.error(f"❌ {title} crashed: {type(e).__name__}: {e}")
        st.exception(e)

def main() -> None:
    st.set_page_config(page_title="KMFFL App", layout="wide")
    st.title("KMFFL App")

    con = get_duckdb_connection()
    tables = load_all_dfs(FILE_MAP, con)

    # REMOVE enforce_minimum_schema call

    df_dict = {}
    for key, table_name in tables.items():
        if table_name:
            df_dict[key] = query_to_df(con, f"SELECT * FROM {table_name}")
        else:
            df_dict[key] = None

    available = {k for k, v in df_dict.items() if v is not None}

    tabs = st.tabs(["Home", "Managers", "Players", "Draft", "Transactions", "Simulations", "Extras"])

    with tabs[0]:
        if "Matchup Data" in available:
            safe_render("Home", display_homepage_overview, df_dict)
        else:
            st.warning("Home requires matchup.parquet")

    with tabs[1]:
        if "Matchup Data" in available:
            safe_render("Managers", display_matchup_overview, df_dict)
        else:
            st.warning("Managers requires matchup.parquet")

    with tabs[2]:
        sub_tabs = st.tabs(["Stats", "Injuries"])
        with sub_tabs[0]:
            player_data = df_dict.get("Player Data")
            matchup_data = df_dict.get("Matchup Data")
            stats_tabs = st.tabs(["Weekly", "Season", "Career"])
            with stats_tabs[0]:
                if player_data is not None and matchup_data is not None:
                    safe_render("Weekly", StreamlitWeeklyPlayerDataViewer(player_data, matchup_data).display)
                else:
                    st.warning("Weekly stats need player.parquet and matchup.parquet")
            with stats_tabs[1]:
                if player_data is not None and matchup_data is not None:
                    safe_render("Season", StreamlitSeasonPlayerDataViewer(player_data, matchup_data).display)
                else:
                    st.warning("Season stats need player.parquet and matchup.parquet")
            with stats_tabs[2]:
                if player_data is not None and matchup_data is not None:
                    safe_render("Career", StreamlitCareerPlayerDataViewer(player_data, matchup_data).display)
                else:
                    st.warning("Career stats need player.parquet and matchup.parquet")
        with sub_tabs[1]:
            injury_ready = df_dict.get("Injury Data")
            player_ready = df_dict.get("Player Data")
            if injury_ready is not None and player_ready is not None:
                if "player" not in injury_ready.columns and "full_name" in injury_ready.columns:
                    injury_ready = injury_ready.rename(columns={"full_name": "player"})
                if "player" in injury_ready.columns:
                    injury_ready["player"] = injury_ready["player"].astype(str).str.strip()
                if "player" in player_ready.columns:
                    player_ready["player"] = player_ready["player"].astype(str).str.strip()

                prepared = {
                    **df_dict,
                    "Injury Data": injury_ready,
                    "Player Data": player_ready,
                }
                safe_render("Injuries", display_injury_overview, prepared)
            else:
                st.info("Injuries need injury.parquet and player.parquet")

    with tabs[3]:
        if "Draft History" in available:
            safe_render("Draft", display_draft_data_overview, df_dict)
        else:
            st.info("Draft requires draft.parquet")

    with tabs[4]:
        needs = {"All Transactions", "Player Data", "Injury Data", "Draft History"}
        if needs.issubset(available):
            safe_render("Transactions", AllTransactionsViewer(
                df_dict["All Transactions"], df_dict["Player Data"],
                df_dict["Injury Data"], df_dict["Draft History"]
            ).display)
        else:
            st.info("Transactions need transactions.parquet, player.parquet, injury.parquet, and draft.parquet")

    with tabs[5]:
        st.header("Simulations")
        if {"Matchup Data", "Player Data"}.issubset(available):
            safe_render("Simulations", display_simulations_viewer,
                        df_dict["Matchup Data"], df_dict["Player Data"])
        else:
            st.info("Simulations need matchup.parquet and player.parquet")

    with tabs[6]:
        extras_tabs = st.tabs(["Graphs", "Keeper", "Team Names"])
        with extras_tabs[0]:
            if df_dict:
                safe_render("Graphs", display_graphs_overview, df_dict)
        with extras_tabs[1]:
            st.header("Keeper")
            if "Player Data" in available:
                safe_render("Keeper", KeeperDataViewer(df_dict["Player Data"]).display)
            else:
                st.info("Keeper requires player.parquet")
        with extras_tabs[2]:
            safe_render("Team Names", display_team_names, df_dict.get("Matchup Data"))

if __name__ == "__main__":
    main()