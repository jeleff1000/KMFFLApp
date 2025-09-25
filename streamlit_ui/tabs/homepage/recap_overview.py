from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime
import re

import pandas as pd
import streamlit as st

from .team_recaps import weekly_recap, season_recap
from . import player_weekly_recap


# ----- Local helpers for selection UI -----
def _as_dataframe(obj: Any) -> Optional[pd.DataFrame]:
    if isinstance(obj, pd.DataFrame):
        return obj
    try:
        if isinstance(obj, (list, tuple)) and obj and isinstance(obj[0], dict):
            return pd.DataFrame(obj)
        if isinstance(obj, dict):
            return pd.DataFrame(obj)
    except Exception:
        return None
    return None


def _get_matchup_df(df_dict: Optional[Dict[Any, Any]]) -> Optional[pd.DataFrame]:
    if not isinstance(df_dict, dict):
        return None
    if "Matchup Data" in df_dict:
        return _as_dataframe(df_dict["Matchup Data"])
    for k, v in df_dict.items():
        if str(k).strip().lower() == "matchup data":
            return _as_dataframe(v)
    return None


def _unique_numeric(df: pd.DataFrame, col: str) -> List[int]:
    if col not in df.columns:
        return []
    ser = pd.to_numeric(df[col], errors="coerce").dropna().astype(int)
    return sorted(ser.unique().tolist())


def _weeks_for_year(df: pd.DataFrame, year: int) -> List[int]:
    if not {"year", "week"}.issubset(set(df.columns)):
        return []
    df_yr = df[pd.to_numeric(df["year"], errors="coerce").astype("Int64") == year]
    if df_yr.empty:
        return []
    return _unique_numeric(df_yr, "week")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower().strip())


def _find_manager_column(df: pd.DataFrame) -> Optional[str]:
    preferred = [
        "manager", "manager_name", "owner", "owner_name",
        "team_owner", "team_manager",
    ]
    cols_lower = {str(c).strip().lower(): c for c in df.columns}
    for p in preferred:
        if p in cols_lower:
            return cols_lower[p]
    for lower, original in cols_lower.items():
        if "manager" in lower or "owner" in lower:
            return original
    return None


def _manager_options(df: Optional[pd.DataFrame]) -> List[str]:
    if df is None:
        return []
    col = _find_manager_column(df)
    if not col:
        return []
    try:
        ser = df[col].astype(str).str.strip()
    except Exception:
        return []
    ser = ser[(ser.notna()) & (ser != "")]
    return sorted(set(ser.tolist()), key=lambda x: x.lower())


# ----- New helpers for Player Data two-week (current + prior cumulative) slice -----
def _get_player_df(df_dict: Optional[Dict[Any, Any]]) -> Optional[pd.DataFrame]:
    if not isinstance(df_dict, dict):
        return None
    if "Player Data" in df_dict:
        return _as_dataframe(df_dict["Player Data"])
    for k, v in (df_dict or {}).items():
        if str(k).strip().lower() == "player data":
            return _as_dataframe(v)
    return None


def _detect_year_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["season_year", "year", "Year", "season", "Season"]:
        if c in df.columns:
            return c
    return None


def _detect_week_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["week", "Week"]:
        if c in df.columns:
            return c
    return None


def _detect_cum_week_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["cumulative_week", "cumulativeweek", "cumul_week", "cumulweek"]:
        if c in df.columns:
            return c
    # fallback
    return _detect_week_col(df)


def _build_player_two_week_slice(player_df: pd.DataFrame,
                                 year: int,
                                 week: int) -> Tuple[pd.DataFrame, Optional[float], Optional[float]]:
    """
    Returns (slice_df, prev_cum_value, current_cum_value).
    Finds the cumulative value(s) for the selected year/week, then prior global cumulative.
    """
    if player_df is None or player_df.empty:
        return player_df.iloc[0:0], None, None

    cum_col = _detect_cum_week_col(player_df)
    week_col = _detect_week_col(player_df)
    year_col = _detect_year_col(player_df)
    if not cum_col or not week_col:
        return player_df.iloc[0:0], None, None

    df = player_df.copy()
    df["_cum_"] = pd.to_numeric(df[cum_col], errors="coerce")
    df["_wk_"] = pd.to_numeric(df[week_col], errors="coerce")
    if year_col:
        df["_yr_"] = pd.to_numeric(df[year_col], errors="coerce")

    if year_col:
        cur_mask = (df["_yr_"] == year) & (df["_wk_"] == week)
    else:
        cur_mask = (df["_wk_"] == week)
    cur_rows = df[cur_mask]
    if cur_rows.empty:
        return df.iloc[0:0], None, None

    cur_cums = cur_rows["_cum_"].dropna().unique()
    if len(cur_cums) == 0:
        return df.iloc[0:0], None, None
    cur_cum = float(max(cur_cums))

    prev_rows = df[df["_cum_"] < cur_cum]
    if prev_rows.empty:
        slice_df = df[df["_cum_"] == cur_cum]
        return slice_df.drop(columns=["_cum_", "_wk_"] + (["_yr_"] if year_col else []), errors="ignore"), None, cur_cum

    prev_cum = float(prev_rows["_cum_"].max())
    slice_df = df[df["_cum_"].isin([prev_cum, cur_cum])]
    return slice_df.drop(columns=["_cum_", "_wk_"] + (["_yr_"] if year_col else []), errors="ignore"), prev_cum, cur_cum


# ----- Main Overview UI -----
def display_recap_overview(df_dict: Optional[Dict[Any, Any]] = None) -> None:
    matchup_df = _get_matchup_df(df_dict)

    mode = st.radio("", options=["Start from Today's Date", "Choose a Date"], horizontal=True)

    selected_year: Optional[int] = None
    selected_week: Optional[int] = None

    if mode == "Start from Today's Date":
        if matchup_df is not None:
            years = _unique_numeric(matchup_df, "year")
            if years:
                selected_year = max(years)
                weeks = _weeks_for_year(matchup_df, selected_year)
                selected_week = max(weeks) if weeks else None
        if selected_year is None:
            selected_year = datetime.now().year
        if selected_week is None:
            selected_week = 1
        st.caption(f"Selected Year: {selected_year} — Week: {selected_week}")
    else:
        if matchup_df is not None:
            years = _unique_numeric(matchup_df, "year") or [datetime.now().year]
        else:
            years = [datetime.now().year]
        col_year, col_week = st.columns(2)
        with col_year:
            selected_year = st.selectbox("Year", options=years, index=len(years) - 1)
        if matchup_df is not None:
            weeks = _weeks_for_year(matchup_df, selected_year) or _unique_numeric(matchup_df, "week")
            if not weeks:
                weeks = list(range(1, 19))
        else:
            weeks = list(range(1, 19))
        with col_week:
            selected_week = st.selectbox("Week", options=weeks, index=len(weeks) - 1)
        st.caption(f"Selected Year: {selected_year} — Week: {selected_week}")

    st.subheader("Manager")
    managers = _manager_options(matchup_df)
    if not managers:
        st.info("No managers found in the dataset.")
        return
    selected_manager = st.selectbox("Select Manager", options=managers, index=0)

    st.session_state["recap_overview_selection"] = {
        "year": selected_year,
        "week": selected_week,
        "manager": selected_manager,
    }

    st.divider()
    st.header("Weekly Recap")
    weekly_recap.display_weekly_recap(
        df_dict=df_dict,
        year=selected_year,
        week=selected_week,
        manager=selected_manager,
    )

    st.divider()
    st.header("Season Analysis")
    season_recap.display_season_recap(
        df_dict=df_dict,
        year=selected_year,
        week=selected_week,
        manager=selected_manager,
    )

    # Build two-week Player Data slice (all owners) for Most Improved / awards
    player_df = _get_player_df(df_dict)
    if player_df is not None:
        two_week_df, prev_cum, cur_cum = _build_player_two_week_slice(player_df, selected_year, selected_week)
        if two_week_df is not None and not two_week_df.empty:
            # Provide contextual info if needed later
            st.session_state["player_prev_cum_week"] = prev_cum
            st.session_state["player_cur_cum_week"] = cur_cum
            df_dict_player = dict(df_dict or {})
            df_dict_player["Player Data"] = two_week_df
        else:
            df_dict_player = df_dict
    else:
        df_dict_player = df_dict

    st.divider()
    st.header("Player Weekly Recap")
    if hasattr(player_weekly_recap, "display_player_weekly_recap"):
        try:
            player_weekly_recap.display_player_weekly_recap(
                df_dict=df_dict_player,
                year=selected_year,
                week=selected_week,
                manager=selected_manager,
            )
        except Exception as e:
            st.warning(f"Player weekly recap failed: {e}")
    else:
        st.warning("`display_player_weekly_recap` not found in module.")