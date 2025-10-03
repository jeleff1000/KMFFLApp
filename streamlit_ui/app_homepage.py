#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Optional

import duckdb
import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------------------
# Import path: ensure repo root is importable for `streamlit_ui.*` absolute imports
# --------------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # parent of the folder containing this file
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Tabs / pages
from streamlit_ui.tabs.matchup_data_and_simulations.matchups.matchup_overview import (
    display_matchup_overview,
)
from streamlit_ui.tabs.keepers.keepers_home import KeeperDataViewer
from streamlit_ui.tabs.matchup_data_and_simulations.simulation_home import (
    display_simulations_viewer,
)
from streamlit_ui.tabs.player_stats.weekly_player_stats_overview import (
    StreamlitWeeklyPlayerDataViewer,
)
from streamlit_ui.tabs.player_stats.season_player_stats_overview import (
    StreamlitSeasonPlayerDataViewer,
)
from streamlit_ui.tabs.player_stats.career_player_stats_overview import (
    StreamlitCareerPlayerDataViewer,
)
from streamlit_ui.tabs.draft_data.draft_data_overview import display_draft_data_overview
from streamlit_ui.tabs.injury_data.injury_overview import display_injury_overview
from streamlit_ui.tabs.transactions.transactions_adds_drops_trades_overview import (
    AllTransactionsViewer,
)
from streamlit_ui.tabs.team_names.team_names import display_team_names
from streamlit_ui.tabs.homepage.homepage_overview import display_homepage_overview
from streamlit_ui.tabs.graphs.graphs_overview import display_graphs_overview


# ======================================================================================
# Config helpers
# ======================================================================================
def _get_env_or_secret(key: str, default: str | None = None) -> str | None:
    """
    Prefer environment variable; if not found, try st.secrets but never crash
    if secrets.toml doesn't exist.
    """
    val = os.environ.get(key)
    if val:
        return val
    try:
        return st.secrets[key]  # may raise if secrets.toml missing
    except Exception:
        return default


# ======================================================================================
# DuckDB connection (one per session)
# ======================================================================================
@st.cache_resource(show_spinner=False)
def get_duckdb_conn() -> duckdb.DuckDBPyConnection:
    """
    Use an in-memory DB by default. If you set PERSISTENT_DUCKDB=/path/file.duckdb
    (env var or st.secrets), we will persist and reuse between runs.
    """
    db_path = _get_env_or_secret("PERSISTENT_DUCKDB", "")
    if db_path:
        return duckdb.connect(database=db_path, read_only=False)
    return duckdb.connect(database=":memory:")


# ======================================================================================
# Data loading via DuckDB
#  - Flexible DATA_DIR: defaults to the folder containing this file but can be overridden.
#  - Case-insensitive filename resolution (helps when moving from Windows -> Linux).
#  - Optional sidebar debug listing to see what the cloud instance can access.
# ======================================================================================
PARQUET_FILES = {
    "Injury Data": "injury.parquet",
    "Schedules": "schedule.parquet",
    "All Transactions": "transactions.parquet",
    "Draft History": "draft.parquet",
    "Player Data": "player.parquet",
    "Matchup Data": "matchup.parquet",
}


def _resolve_data_dir() -> Path:
    """
    Resolve where Parquet files live.
    - DATA_DIR (env or secrets) wins if present.
    - Otherwise, default to the folder next to this script.
    """
    data_dir = _get_env_or_secret("DATA_DIR", "")
    if data_dir:
        return Path(data_dir).expanduser().resolve()
    return Path(__file__).resolve().parent


def _case_insensitive_find(folder: Path, target_name: str) -> Optional[Path]:
    """
    Try to find a file in `folder` matching `target_name` in a case-insensitive way.
    Returns the resolved path if found, else None.
    """
    target_lower = target_name.lower()
    try:
        for p in folder.iterdir():
            if p.is_file() and p.name.lower() == target_lower:
                return p.resolve()
    except Exception:
        pass
    return None


def _list_parquet_files(folder: Path) -> list[str]:
    try:
        return sorted([p.name for p in folder.glob("*.parquet")])
    except Exception:
        return []


def _read_parquet_with_duckdb(conn: duckdb.DuckDBPyConnection, path: Path) -> pd.DataFrame:
    """
    Read Parquet using DuckDB. We use parquet_scan so DuckDB can push down filters if needed.
    Safely escape single quotes in the path for SQL.
    """
    safe_path = str(path).replace("'", "''")
    query = f"SELECT * FROM parquet_scan('{safe_path}')"
    return conn.execute(query).df()


@st.cache_data(show_spinner=False)
def load_duckdb_dfs(debug: bool = False) -> Dict[str, Optional[pd.DataFrame]]:
    """
    Load all required Parquet files into pandas DataFrames via DuckDB.
    Shows friendly warnings for missing files and a debug listing if requested.
    """
    data_dir = _resolve_data_dir()
    if debug:
        st.info(f"Looking for data in: {data_dir}")
        st.caption(f"Parquet files found: {_list_parquet_files(data_dir) or '[none]'}")

    conn = get_duckdb_conn()

    df_dict: Dict[str, Optional[pd.DataFrame]] = {}
    for key, fname in PARQUET_FILES.items():
        # Resolve path case-insensitively to avoid Windows->Linux surprises
        path = (data_dir / fname).resolve()
        if not path.exists():
            ci = _case_insensitive_find(data_dir, fname)
            if ci is not None:
                path = ci

        try:
            if not path.exists():
                st.warning(f"Missing file for '{key}': {data_dir / fname}")
                df_dict[key] = None
                continue

            df = _read_parquet_with_duckdb(conn, path)
            df_dict[key] = df

        except Exception as e:
            # Keep running even if one file fails
            st.error(f"Failed to read {path} ({key}): {e}")
            df_dict[key] = None

    return df_dict


# ======================================================================================
# Small helpers for the Injuries tab (kept from your original design)
# ======================================================================================
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


def _prepare_df_dict_for_injuries(df_dict: Dict[str, Optional[pd.DataFrame]]) -> Dict[str, Optional[pd.DataFrame]]:
    if not df_dict:
        return df_dict

    prepared = dict(df_dict)
    injury_df = df_dict.get("Injury Data")
    player_df = df_dict.get("Player Data")

    prepared["Injury Data"] = _normalize_merge_keys(injury_df, rename_full_name=True) if injury_df is not None else None
    prepared["Player Data"] = _normalize_merge_keys(player_df, rename_full_name=False) if player_df is not None else None
    return prepared


# ======================================================================================
# Streamlit UI
# ======================================================================================
def _apply_safe_mode_filters(df_dict: Dict[str, Optional[pd.DataFrame]], *, recent_weeks: int = 8) -> Dict[str, Optional[pd.DataFrame]]:
    """
    Reduce dataset size to avoid OOM on initial render.
    - Keeps only the most recent season in Matchup Data and last `recent_weeks` weeks.
    """
    out = dict(df_dict)
    md = out.get("Matchup Data")
    if md is not None and {"year", "week"}.issubset(md.columns) and not md.empty:
        try:
            # ensure numeric
            md = md.copy()
            md["year"] = pd.to_numeric(md["year"], errors="coerce")
            md["week"] = pd.to_numeric(md["week"], errors="coerce")
            md = md.dropna(subset=["year", "week"])
            latest_year = int(md["year"].max())
            recent = sorted(md.loc[md["year"] == latest_year, "week"].unique())[-recent_weeks:]
            out["Matchup Data"] = md[(md["year"] == latest_year) & (md["week"].isin(recent))].copy()
        except Exception as e:
            st.warning(f"Safe mode filter skipped (Matchup Data): {e}")
    return out


def main():
    st.set_page_config(page_title="KMFFL App", layout="wide")

    with st.sidebar:
        debug = st.checkbox("Debug data paths", value=False)
        safe_mode = st.checkbox("Safe mode (reduce data)", value=True,
                                help="Limits Matchup Data to the latest season and last few weeks to prevent OOM on first load.")
        recent_weeks = st.number_input("Recent weeks to keep (safe mode)", min_value=1, max_value=18, value=8, step=1)
        st.caption("Tip: Set DATA_DIR (env or secrets) to your parquet folder.")
        st.caption("Optional: Set PERSISTENT_DUCKDB to persist the DuckDB database on disk.")

    st.title("KMFFL App")

    df_dict = load_duckdb_dfs(debug=debug)
    if not df_dict:
        st.error("No data loaded.")
        return

    if safe_mode:
        df_dict = _apply_safe_mode_filters(df_dict, recent_weeks=int(recent_weeks))

    tab_names = ["Home", "Managers", "Players", "Draft", "Transactions", "Simulations", "Extras"]
    tabs = st.tabs(tab_names)

    for i, tab_name in enumerate(tab_names):
        with tabs[i]:
            try:
                if tab_name == "Home":
                    display_homepage_overview(df_dict)

                elif tab_name == "Managers":
                    # Defensive: ensure expected columns exist before rendering heavy views
                    md = df_dict.get("Matchup Data")
                    if md is None or md.empty:
                        st.warning("Matchup Data not found.")
                    else:
                        display_matchup_overview(df_dict)

                elif tab_name == "Players":
                    sub_tabs = st.tabs(["Stats", "Injuries"])

                    # ---- Stats
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

                    # ---- Injuries
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

            except Exception as e:
                # Never let a tab crash the whole app
                st.error(f"An error occurred rendering '{tab_name}': {e}")
                st.exception(e)


if __name__ == "__main__":
    main()
