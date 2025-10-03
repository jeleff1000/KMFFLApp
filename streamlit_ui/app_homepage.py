#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Iterable

import duckdb
import pandas as pd
import streamlit as st

# =========================
# Repo root / imports
# =========================
APP_FILE = Path(__file__).resolve()
APP_DIR = APP_FILE.parent      # .../KMFFLApp/streamlit_ui

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

# Your modules
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

# =========================
# Data location (same folder as this file)
# =========================
# You can override with KMFFL_DATA_DIR if you ever move files to a different folder.
DATA_DIR = Path(os.getenv("KMFFL_DATA_DIR", APP_DIR)).resolve()

# Exact filenames you showed:
FILE_MAP = {
    "Matchup Data": DATA_DIR / "matchup.parquet",
    "Player Data": DATA_DIR / "player.parquet",
    "Schedules": DATA_DIR / "schedule.parquet",
    "All Transactions": DATA_DIR / "transactions.parquet",
    "Draft History": DATA_DIR / "draft.parquet",
    "Injury Data": DATA_DIR / "injury.parquet",
}

# =========================
# DuckDB helpers
# =========================
@st.cache_resource
def get_duckdb_conn() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(database=":memory:")

def _read_parquet(conn: duckdb.DuckDBPyConnection, path: Path) -> pd.DataFrame:
    safe_path = str(path).replace("'", "''")
    q = f"SELECT * FROM parquet_scan('{safe_path}')"
    return conn.execute(q).df()

@st.cache_data(show_spinner=False)
def load_duckdb_dfs(file_map: Dict[str, Path]) -> Dict[str, Optional[pd.DataFrame]]:
    """
    Loads all datasets from DATA_DIR; missing files become None and are gated in the UI.
    """
    conn = get_duckdb_conn()
    dfs: Dict[str, Optional[pd.DataFrame]] = {}

    # Diagnostics in UI
    st.caption(f"Working directory: `{os.getcwd()}`")
    st.caption(f"App file: `{APP_FILE}`")
    st.caption(f"Repo root: `{REPO_ROOT}`")
    st.caption(f"Data dir: `{DATA_DIR}`")

    for key, path in file_map.items():
        if not path.exists():
            st.error(f"Missing data: **{key}** → `{path}` not found.")
            dfs[key] = None
            continue
        try:
            dfs[key] = _read_parquet(conn, path)
        except Exception as e:
            st.exception(RuntimeError(f"Failed to read {path}: {e}"))
            dfs[key] = None

    return dfs

# =========================
# Hygiene helpers
# =========================
def _normalize_merge_keys(df: Optional[pd.DataFrame], *, rename_full_name: bool = False) -> Optional[pd.DataFrame]:
    if df is None or df.empty:
        return df
    out = df.copy()
    if rename_full_name and "player" not in out.columns and "full_name" in out.columns:
        out = out.rename(columns={"full_name": "player"})
    if "player" in out.columns:
        out["player"] = out["player"].astype(str).str.strip()
    if "week" in out.columns:
        out["week"] = pd.to_numeric(out["week"], errors="coerce")
    if "season" in out.columns:
        out["season"] = pd.to_numeric(out["season"], errors="coerce")
    keys = [c for c in ("player", "week", "season") if c in out.columns]
    if set(keys) == {"player", "week", "season"}:
        out = out.dropna(subset=["player", "week", "season"])
        out["week"] = out["week"].astype("int64")
        out["season"] = out["season"].astype("int64")
    return out

def _prepare_df_dict_for_injuries(df_dict: Dict[str, Optional[pd.DataFrame]]) -> Dict[str, Optional[pd.DataFrame]]:
    if not df_dict:
        return df_dict
    prepared = dict(df_dict)
    prepared["Injury Data"] = _normalize_merge_keys(df_dict.get("Injury Data"), rename_full_name=True)
    prepared["Player Data"] = _normalize_merge_keys(df_dict.get("Player Data"), rename_full_name=False)
    return prepared

# =========================
# App (with gated tabs)
# =========================
def main() -> None:
    st.set_page_config(page_title="KMFFL App", layout="wide")
    st.title("KMFFL App")

    df_dict = load_duckdb_dfs(FILE_MAP)
    available = {k for k, v in df_dict.items() if v is not None}

    tab_names = ["Home", "Managers", "Players", "Draft", "Transactions", "Simulations", "Extras"]
    tabs = st.tabs(tab_names)

    # ---- Home (needs Matchup Data)
    with tabs[0]:
        if "Matchup Data" in available:
            display_homepage_overview(df_dict)
        else:
            st.warning("Home view requires **Matchup Data** (matchup.parquet).")

    # ---- Managers (needs Matchup Data)
    with tabs[1]:
        if "Matchup Data" in available:
            display_matchup_overview(df_dict)
        else:
            st.warning("Managers view requires **Matchup Data** (matchup.parquet).")

    # ---- Players
    with tabs[2]:
        sub_tabs = st.tabs(["Stats", "Injuries"])
        with sub_tabs[0]:
            player_data = df_dict.get("Player Data")
            matchup_data = df_dict.get("Matchup Data")
            stats_tabs = st.tabs(["Weekly", "Season", "Career"])
            with stats_tabs[0]:
                if player_data is not None and matchup_data is not None:
                    StreamlitWeeklyPlayerDataViewer(player_data, matchup_data).display()
                else:
                    st.warning("Weekly stats need **player.parquet** and **matchup.parquet**.")
            with stats_tabs[1]:
                if player_data is not None and matchup_data is not None:
                    StreamlitSeasonPlayerDataViewer(player_data, matchup_data).display()
                else:
                    st.warning("Season stats need **player.parquet** and **matchup.parquet**.")
            with stats_tabs[2]:
                if player_data is not None and matchup_data is not None:
                    StreamlitCareerPlayerDataViewer(player_data, matchup_data).display()
                else:
                    st.warning("Career stats need **player.parquet** and **matchup.parquet**.")
        with sub_tabs[1]:
            prepared = _prepare_df_dict_for_injuries(df_dict)
            if prepared.get("Injury Data") is not None and prepared.get("Player Data") is not None:
                display_injury_overview(prepared)
            else:
                st.info("Injuries will show once **injury.parquet** (and **player.parquet**) are present.")

    # ---- Draft (needs Draft History)
    with tabs[3]:
        if "Draft History" in available:
            display_draft_data_overview(df_dict)
        else:
            st.info("Draft tab requires **draft.parquet**.")

    # ---- Transactions (needs All Transactions + Player + Injury + Draft)
    with tabs[4]:
        needs = {"All Transactions", "Player Data", "Injury Data", "Draft History"}
        if needs.issubset(available):
            AllTransactionsViewer(
                df_dict["All Transactions"], df_dict["Player Data"], df_dict["Injury Data"], df_dict["Draft History"]
            ).display()
        else:
            st.info("Transactions need **transactions.parquet**, **player.parquet**, **injury.parquet**, and **draft.parquet**.")

    # ---- Simulations (needs Matchup + Player)
    with tabs[5]:
        st.header("Simulations")
        if {"Matchup Data", "Player Data"}.issubset(available):
            display_simulations_viewer(df_dict["Matchup Data"], df_dict["Player Data"])
        else:
            st.info("Simulations need **matchup.parquet** and **player.parquet**.")

    # ---- Extras
    with tabs[6]:
        extras_tabs = st.tabs(["Graphs", "Keeper", "Team Names"])
        with extras_tabs[0]:
            if df_dict:
                display_graphs_overview(df_dict)
            else:
                st.info("Graphs will render when datasets are present.")
        with extras_tabs[1]:
            st.header("Keeper")
            if "Player Data" in available:
                KeeperDataViewer(df_dict["Player Data"]).display()
            else:
                st.info("Keeper view needs **player.parquet**.")
        with extras_tabs[2]:
            display_team_names(df_dict.get("Matchup Data"))

# =========================
# Entrypoint
# =========================
if __name__ == "__main__":
    main()
