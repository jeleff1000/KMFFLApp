#!/usr/bin/env python3
# KMFFL Streamlit app — Polars-only parquet loading

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Callable, Any

import pandas as pd
import polars as pl
import streamlit as st

# =============================================================================
# Repo root / imports
# =============================================================================
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

# =============================================================================
# Data location
# =============================================================================
DATA_DIR = Path(os.getenv("KMFFL_DATA_DIR", APP_DIR)).resolve()
FILE_MAP: Dict[str, Path] = {
    "Matchup Data": DATA_DIR / "matchup.parquet",
    "Player Data": DATA_DIR / "player.parquet",
    "Schedules": DATA_DIR / "schedule.parquet",
    "All Transactions": DATA_DIR / "transactions.parquet",
    "Draft History": DATA_DIR / "draft.parquet",
    "Injury Data": DATA_DIR / "injury.parquet",
}


# =============================================================================
# Parquet reader
# =============================================================================
@st.cache_data(show_spinner=False)
def read_parquet(path: Path) -> pd.DataFrame:
    df_pl = pl.read_parquet(path)
    return df_pl.to_pandas(use_pyarrow_extension_array=True)


@st.cache_data(show_spinner=False)
def load_all_dfs(file_map: Dict[str, Path]) -> Dict[str, Optional[pd.DataFrame]]:
    dfs = {}
    for key, path in file_map.items():
        if not path.exists():
            dfs[key] = None
            continue
        try:
            dfs[key] = read_parquet(path)
        except Exception:
            dfs[key] = None
    return dfs


# =============================================================================
# Schema normalization
# =============================================================================
def _normalize_merge_keys(df: Optional[pd.DataFrame], *, rename_full_name: bool = False) -> Optional[pd.DataFrame]:
    if df is None or df.empty:
        return df
    out = df.copy()
    if rename_full_name and "player" not in out.columns and "full_name" in out.columns:
        out = out.rename(columns={"full_name": "player"})
    if "player" in out.columns:
        out["player"] = out["player"].astype(str).str.strip()
    for c in ("week", "season", "year"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    keys = [c for c in ("player", "week", "season") if c in out.columns]
    if set(keys) == {"player", "week", "season"}:
        out = out.dropna(subset=keys)
        out["week"] = out["week"].astype("int64")
        out["season"] = out["season"].astype("int64")
    return out


def enforce_minimum_schema(df_dict: Dict[str, Optional[pd.DataFrame]]) -> Dict[str, Optional[pd.DataFrame]]:
    out = dict(df_dict)
    mdf = out.get("Matchup Data")
    sdf = out.get("Schedules")

    if mdf is not None:
        mdf = mdf.copy()
        if "opponent_score" not in mdf.columns and "opponent_points" in mdf.columns:
            mdf["opponent_score"] = mdf["opponent_points"]
        if "team_score" not in mdf.columns and "team_points" in mdf.columns:
            mdf["team_score"] = mdf["team_points"]
        for c in ("year", "week"):
            if c in mdf.columns:
                mdf[c] = pd.to_numeric(mdf[c], errors="coerce")
        for col, default in [("is_playoffs", 0), ("is_consolation", 0)]:
            if col not in mdf.columns:
                mdf[col] = default

        if sdf is not None and not sdf.empty:
            join_keys = [k for k in ("year", "week", "manager", "opponent") if k in mdf.columns and k in sdf.columns]
            if join_keys:
                sched_cols = [c for c in ("is_playoffs", "is_consolation", "opponent_score") if c in sdf.columns]
                flags = sdf[join_keys + sched_cols].drop_duplicates()
                mdf = mdf.merge(flags, on=join_keys, how="left", suffixes=("", "_sched"))
                for col in ("is_playoffs", "is_consolation", "opponent_score"):
                    if f"{col}_sched" in mdf.columns:
                        mdf[col] = mdf[f"{col}_sched"].fillna(mdf.get(col))
                        mdf.drop(columns=[f"{col}_sched"], inplace=True)

        if "is_consolation" in mdf.columns and "is_playoffs" in mdf.columns:
            mdf.loc[mdf["is_consolation"].fillna(0).astype(int) == 1, "is_playoffs"] = 0

        out["Matchup Data"] = mdf

    return out


# =============================================================================
# Safe render wrapper
# =============================================================================
def safe_render(title: str, fn: Callable[..., Any], *args, **kwargs) -> None:
    try:
        fn(*args, **kwargs)
    except Exception as e:
        st.error(f"❌ {title} crashed: {type(e).__name__}: {e}")
        st.exception(e)


# =============================================================================
# App
# =============================================================================
def main() -> None:
    st.set_page_config(page_title="KMFFL App", layout="wide")
    st.title("KMFFL App")

    df_dict = load_all_dfs(FILE_MAP)
    df_dict = enforce_minimum_schema(df_dict)
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
                prepared = {
                    **df_dict,
                    "Injury Data": _normalize_merge_keys(injury_ready, rename_full_name=True),
                    "Player Data": _normalize_merge_keys(player_ready, rename_full_name=False),
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