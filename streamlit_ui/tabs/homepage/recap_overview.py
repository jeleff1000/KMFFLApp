# streamlit_ui/tabs/homepage/recap_overview.py
from typing import Any, Dict, Optional, List
from datetime import datetime
import re

import pandas as pd
import streamlit as st

# Import the two recap text generators (no UI inside these)
from .team_recaps import weekly_recap, season_recap


# ----- Local helpers for selection UI (kept here to avoid cross‑module "private" imports) -----
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


# ----- Main Overview (owns all selection UI) -----
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

    # Persist selection for downstream modules if needed
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