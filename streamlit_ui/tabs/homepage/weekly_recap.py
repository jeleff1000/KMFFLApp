from typing import Any, Dict, Optional
from datetime import datetime
import re

import pandas as pd
import streamlit as st


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


def _unique_numeric(df: pd.DataFrame, col: str) -> list[int]:
    if col not in df.columns:
        return []
    ser = pd.to_numeric(df[col], errors="coerce").dropna().astype(int)
    return sorted(ser.unique().tolist())


def _weeks_for_year(df: pd.DataFrame, year: int) -> list[int]:
    if not {"year", "week"}.issubset(set(df.columns)):
        return []
    df_yr = df[pd.to_numeric(df["year"], errors="coerce").astype("Int64") == year]
    if df_yr.empty:
        return []
    return _unique_numeric(df_yr, "week")


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


def _manager_options(df: pd.DataFrame) -> list[str]:
    col = _find_manager_column(df)
    if not col:
        return []
    try:
        ser = df[col].astype(str).str.strip()
    except Exception:
        return []
    ser = ser[(ser.notna()) & (ser != "")]
    opts = sorted(set(ser.tolist()), key=lambda x: x.lower())
    return opts


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower().strip())


def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    norm_map = {_norm(c): c for c in df.columns}
    for cand in candidates:
        key = _norm(cand)
        if key in norm_map:
            return norm_map[key]
    return None


def _val(row: pd.Series, col: Optional[str], default=None):
    if not col:
        return default
    try:
        v = row[col]
        if pd.isna(v):
            return default
        return v
    except Exception:
        return default


def _to_int(v, default=None) -> Optional[int]:
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return default
        return int(float(v))
    except Exception:
        return default


def _to_float(v, default=None) -> Optional[float]:
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return default
        return float(v)
    except Exception:
        return default


def _flag(v) -> Optional[int]:
    # Return 1 for truthy, 0 for falsy, None if unknown.
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, bool):
        return 1 if v else 0
    try:
        f = float(v)
        if not pd.isna(f):
            return 1 if int(f) != 0 else 0
    except Exception:
        pass
    s = str(v).strip().lower()
    if s in {"true", "t", "yes", "y", "win", "w"}:
        return 1
    if s in {"false", "f", "no", "n", "loss", "l"}:
        return 0
    return None


def _fmt_points(v) -> str:
    f = _to_float(v, None)
    if f is None:
        return "N/A"
    return f"{f:.1f}".rstrip("0").rstrip(".")


def _fmt_number(v) -> str:
    f = _to_float(v, None)
    if f is None:
        return "N/A"
    return f"{f:.2f}".rstrip("0").rstrip(".")


def _fmt_percent(v) -> str:
    f = _to_float(v, None)
    if f is None:
        return "N/A"
    pct = f * 100.0 if 0.0 <= f <= 1.0 else f
    return f"{pct:.1f}%".replace(".0%", "%")


def _fmt_abs_number(v) -> str:
    f = _to_float(v, None)
    if f is None:
        return "N/A"
    return _fmt_number(abs(f))


def _combo_projection_message(
    row: pd.Series,
    opponent: str,
    col_win: Optional[str],
    col_above_proj: Optional[str],
    col_projected_wins: Optional[str],
    col_win_ats: Optional[str],
    col_expected_odds: Optional[str],
    col_expected_spread: Optional[str],
    col_margin: Optional[str],
    col_proj_score_err: Optional[str],
    col_abs_proj_score_err: Optional[str],
) -> Optional[str]:
    # Resolve required flags
    win_flag = _flag(_val(row, col_win, None))
    above_flag = _flag(_val(row, col_above_proj, None))
    projwin_flag = _flag(_val(row, col_projected_wins, None))
    winats_flag = _flag(_val(row, col_win_ats, None))
    if None in (win_flag, above_flag, projwin_flag, winats_flag):
        return None

    # Pull numeric fields
    expected_odds = _val(row, col_expected_odds, None)
    expected_odds_num = _to_float(expected_odds, None)

    expected_spread = _to_float(_val(row, col_expected_spread, None), None)
    margin = _to_float(_val(row, col_margin, None), None)
    proj_err = _to_float(_val(row, col_proj_score_err, None), None)
    abs_proj_err = _to_float(_val(row, col_abs_proj_score_err, None), None)
    if abs_proj_err is None and proj_err is not None:
        abs_proj_err = abs(proj_err)

    # Preformatted strings
    odds_pct = _fmt_percent(expected_odds)
    if expected_odds_num is None:
        inv_odds_pct = "N/A"
    else:
        inv_odds_pct = _fmt_percent(1 - expected_odds_num) if 0.0 <= expected_odds_num <= 1.0 else _fmt_percent(100 - expected_odds_num)

    spread_str = _fmt_number(expected_spread) if expected_spread is not None else "N/A"
    spread_flip_str = _fmt_number(-expected_spread) if expected_spread is not None else "N/A"
    margin_pos_str = _fmt_number(abs(margin)) if margin is not None else "N/A"
    proj_err_pos_str = _fmt_number(abs(proj_err)) if proj_err is not None else "N/A"
    abs_proj_err_str = _fmt_number(abs(abs_proj_err)) if abs_proj_err is not None else "N/A"

    w, a, pw, ats = win_flag, above_flag, projwin_flag, winats_flag

    if (w, a, pw, ats) == (0, 0, 0, 0):
        return (
            f"The haters said you couldn't do it and the haters were right! Shout out to the haters! "
            f"We expected you to lose, but not like this. When you saw {opponent} was a {inv_odds_pct} favorite, "
            f"you guys just decided to pack it in losing by {margin_pos_str} compared to the {spread_flip_str} point spread going into the week. "
            f"Maybe a players-only meeting can sort out this debacle."
        )
    if (w, a, pw, ats) == (0, 0, 0, 1):
        return (
            f"{opponent} knew he could go easy on you this week and you proved him right. "
            f"Sure your {margin_pos_str} point loss was closer than the {spread_flip_str} spread going into the week, but you still lost. "
            f"You missed your personal projection by {abs_proj_err_str}. "
            f"You lost but at least you kept it close? Not much good to take from this one. They are who you thought they were! And you let them off the hook!"
        )
    if (w, a, pw, ats) == (0, 0, 1, 0):
        return (
            f"Now I know this one hurts. You had a {inv_odds_pct} chance of winning this matchup going into the week and then… well I don't need to tell you what happened. "
            f"You lost by {margin_pos_str} when you were expected to win by {spread_str}. "
            f"You even missed your personal projections by {abs_proj_err_str}. Scrap that entire gameplan because you won't make it far playing like this."
        )
    if (w, a, pw, ats) == (0, 1, 0, 0):
        return (
            f"You gave it your best but {opponent}'s best was better. "
            f"You exceeded your projected score by {proj_err_pos_str}. Goliath beat David this week but at least you gave it your all."
        )
    if (w, a, pw, ats) == (0, 1, 0, 1):
        return (
            f"You came out fighting this week. The projections had you losing by {spread_flip_str} but you got this game pretty close. "
            f"Only losing by {margin_pos_str}. You exceeded your projections by {proj_err_pos_str} just not enough to pull off the upset."
        )
    if (w, a, pw, ats) == (0, 1, 1, 0):
        return (
            f"{opponent} had something to prove this week! You deserved better. "
            f"You beat your projection by {proj_err_pos_str} but still lost a game where you were favored. Just remember, defense wins championships."
        )
    if (w, a, pw, ats) == (1, 0, 0, 1):
        return (
            f"Sometimes your opponent decides to help you out. Despite a {odds_pct} chance of winning coming into the week and "
            f"missing your expected point total by {abs_proj_err_str}, you still came away with the victory. Way to go!"
        )
    if (w, a, pw, ats) == (1, 0, 1, 0):
        return (
            f"The great teams can win ugly. Sure you only won by {margin_pos_str} compared to the {spread_str} margin entering the week, "
            f"but hey a win is a win!"
        )
    if (w, a, pw, ats) == (1, 0, 1, 1):
        return (
            f"Did you and {opponent} agree to take it easy on each other this week? "
            f"You missed your projected score by {abs_proj_err_str} but still came away with the {margin_pos_str} point victory. Way to go!"
        )
    if (w, a, pw, ats) == (1, 1, 0, 1):
        return (
            f"Everyone doubted you but you pulled through! You won despite the odds makers only giving you a {odds_pct} chance of winning at the beginning of the week. "
            f"You exceeded your projected score by {proj_err_pos_str} and stepped up for a big win!"
        )
    if (w, a, pw, ats) == (1, 1, 1, 0):
        return (
            f"{opponent} gave you everything they got but it wasn't enough to stop your boys. "
            f"Sure you only won by {margin_pos_str} but close only counts in horseshoes and grenades."
        )
    if (w, a, pw, ats) == (1, 1, 1, 1):
        return (
            f"You exceeded your lofty expectations! You had a {odds_pct} chance of winning and won by {margin_pos_str}, "
            f"we had you pegged for a {spread_str} point favorite going into the week."
        )

    return None


def display_weekly_recap(df_dict: Optional[Dict[Any, Any]] = None) -> None:
    matchup_df = _get_matchup_df(df_dict)
    st.subheader("Date Selection")
    mode = st.radio("", options=["Start from Today's Date", "Choose a Date"], horizontal=True)

    selected_year: Optional[int] = None
    selected_week: Optional[int] = None

    if matchup_df is not None:
        df_all = matchup_df.copy()
    else:
        df_all = pd.DataFrame()

    # Detect columns once
    col_manager = _find_manager_column(df_all) if not df_all.empty else None
    col_year = _find_col(df_all, ["year", "season", "season_year", "yr", "manager_year"])
    col_week = _find_col(df_all, ["week", "wk", "manager_week"])

    def _unique_numeric_safe(frame: pd.DataFrame, column: Optional[str]) -> list[int]:
        if frame is None or frame.empty or not column or column not in frame.columns:
            return []
        ser = pd.to_numeric(frame[column], errors="coerce").dropna().astype(int)
        return sorted(ser.unique().tolist())

    # ---- Date selection (with safe fallbacks) ----
    if mode == "Start from Today's Date":
        years_all = _unique_numeric_safe(df_all, col_year) or [datetime.now().year]
        selected_year = max(years_all)
        if col_year:
            pool = df_all[pd.to_numeric(df_all[col_year], errors="coerce").astype("Int64") == selected_year]
        else:
            pool = df_all
        weeks_all = _unique_numeric_safe(pool, col_week) or list(range(1, 19))
        selected_week = max(weeks_all)
        st.caption(f"Selected Year: {selected_year} — Week: {selected_week}")
    else:
        years = _unique_numeric_safe(df_all, col_year) or [datetime.now().year]
        col_y, col_w = st.columns(2)
        with col_y:
            selected_year = st.selectbox("Year", options=years, index=len(years) - 1)
        if not df_all.empty and col_year:
            pool = df_all[pd.to_numeric(df_all[col_year], errors="coerce").astype("Int64") == selected_year]
            weeks = _unique_numeric_safe(pool, col_week) or list(range(1, 19))
        else:
            weeks = list(range(1, 19))
        with col_w:
            selected_week = st.selectbox("Week", options=weeks, index=len(weeks) - 1)
        st.caption(f"Selected Year: {selected_year} — Week: {selected_week}")

    # ---- Manager selection ----
    st.subheader("Manager Selection")
    manager_options = _manager_options(df_all) if not df_all.empty else []
    if not manager_options:
        st.info("No managers found in the dataset.")
        return
    selected_manager = st.selectbox("Select Manager", options=manager_options, index=0)

    st.session_state["weekly_recap_selection"] = {"year": selected_year, "week": selected_week, "manager": selected_manager}
    st.divider()
    st.subheader("Weekly Recap")

    if df_all.empty:
        st.info("No `Matchup Data` dataset available.")
        return

    # ---- Robust filtering (manager -> year -> week) ----
    df = df_all.copy()
    if col_manager:
        df = df[df[col_manager].astype(str).str.strip() == str(selected_manager).strip()]

    if col_year and not df.empty:
        years_for_mgr = _unique_numeric_safe(df, col_year)
        if years_for_mgr and selected_year not in years_for_mgr:
            selected_year = max(years_for_mgr)
        df = df[pd.to_numeric(df[col_year], errors="coerce").astype("Int64") == selected_year]

    if col_week and not df.empty:
        weeks_for_mgr_year = _unique_numeric_safe(df, col_week)
        if weeks_for_mgr_year and selected_week not in weeks_for_mgr_year:
            selected_week = max(weeks_for_mgr_year)
        df = df[pd.to_numeric(df[col_week], errors="coerce").astype("Int64") == selected_week]

    if df.empty:
        st.warning("No record found for that Manager/Year/Week. Try another week or year.")
        if col_year and col_week and col_manager:
            avail = df_all[df_all[col_manager].astype(str).str.strip() == str(selected_manager).strip()]
            if not avail.empty:
                yrs = _unique_numeric_safe(avail, col_year)
                wk_by_yr = {y: _unique_numeric_safe(
                    avail[pd.to_numeric(avail[col_year], errors='coerce').astype('Int64') == y], col_week
                ) for y in yrs}
                st.caption(f"Available for {selected_manager}: {wk_by_yr}")
        return

    # ---- Resolve the rest of the columns ONCE (works with your snake_case) ----
    col_opponent         = _find_col(df, ["opponent", "opponent_team", "opp"])
    col_team_points      = _find_col(df, ["team_points", "team score", "score", "points_for", "points for", "real_score"])
    col_opponent_score   = _find_col(df, ["opponent_score", "opponent score", "opp_points", "points_against", "points against", "opp score", "real_opponent_score"])
    col_weekly_mean      = _find_col(df, ["weekly_mean", "week_mean", "league_weekly_mean", "league_week_mean"])
    col_weekly_median    = _find_col(df, ["weekly_median", "week_median", "league_weekly_median", "league_week_median"])
    col_teams_beat       = _find_col(df, ["teams_beat_this_week", "teams beat this week", "would_beat"])
    col_wins_to_date     = _find_col(df, ["wins_to_date", "Wins to Date"])
    col_losses_to_date   = _find_col(df, ["losses_to_date", "Losses to Date"])
    col_seed_to_date     = _find_col(df, ["playoff_seed_to_date", "Playoff Seed to Date", "seed to date"])
    col_avg_seed         = _find_col(df, ["avg_seed", "average_seed"])
    col_p_playoffs       = _find_col(df, ["p_playoffs", "prob_playoffs", "p playoffs"])
    col_p_champ          = _find_col(df, ["p_champ", "prob_championship", "p champ"])
    col_is_playoffs      = _find_col(df, ["is_playoffs", "is playoffs", "is_playoff", "playoffs", "postseason", "is_postseason"])
    col_win              = _find_col(df, ["win", "won", "is_win", "is win", "result", "w"])
    col_close_margin     = _find_col(df, ["close_margin", "close margin", "is_close", "is close", "close_game", "close game", "nail_biter"])
    col_above_league_med = _find_col(df, ["above_league_median", "above league median", "above_median", "above median"])

    # Projections (your snake_case)
    col_above_proj       = _find_col(df, ["above_proj_score", "Above Projected Score", "above_projected_score", "above proj"])
    col_projected_wins   = _find_col(df, ["proj_wins", "Projected Wins", "projected_wins", "is_favored", "favored"])
    col_win_ats          = _find_col(df, ["win_vs_spread", "Win Matchup Against the Spread", "win_ats", "covered", "cover", "beat_spread"])
    col_expected_odds    = _find_col(df, ["expected_odds", "Expected Odds", "win_probability", "proj_win_prob", "odds"])
    col_expected_spread  = _find_col(df, ["expected_spread", "Expected Spread", "proj_spread", "spread"])
    col_margin           = _find_col(df, ["margin", "score_margin", "point_diff", "points_diff", "margin_of_victory", "real_margin"])
    col_proj_score_err   = _find_col(df, ["proj_score_error", "Projected Score Error", "projected_score_error", "projection_error"])
    col_abs_proj_err     = _find_col(df, ["abs_proj_score_error", "Absolute Value Projected Score Error", "abs_projected_score_error"])

    # ---- Render recap for the first (and only) row after filtering ----
    row = df.iloc[0]
    opponent   = _val(row, col_opponent, "Unknown")
    team_pts   = _val(row, col_team_points, None)
    opp_pts    = _val(row, col_opponent_score, None)
    weekly_mean   = _val(row, col_weekly_mean, None)
    weekly_median = _val(row, col_weekly_median, None)
    teams_beat    = _to_int(_val(row, col_teams_beat, None), None)
    wins_to_date  = _to_int(_val(row, col_wins_to_date, None), None)
    losses_to_date= _to_int(_val(row, col_losses_to_date, None), None)
    seed_to_date  = _to_int(_val(row, col_seed_to_date, None), None)
    avg_seed      = _val(row, col_avg_seed, None)
    p_playoffs    = _val(row, col_p_playoffs, None)
    p_champ       = _val(row, col_p_champ, None)

    final_line = f"The final score of your matchup against {opponent} was {_fmt_points(team_pts)} - {_fmt_points(opp_pts)}."
    is_p    = (_flag(_val(row, col_is_playoffs, None)) == 1)
    did_win = (_flag(_val(row, col_win, None)) == 1)
    close   = (_flag(_val(row, col_close_margin, None)) == 1)
    scenario_msg = None
    if is_p and did_win and close: scenario_msg = "Way to win a close game in the playoffs!"
    elif is_p and did_win:         scenario_msg = "Congrats on the easy playoff win, never in doubt!"
    elif is_p and close and not did_win: scenario_msg = "Lost your playoff game in a nail-biter, better luck next year!"
    elif did_win and close:        scenario_msg = "Way to win a nail-biter!"
    elif close and not did_win:    scenario_msg = "Tough way to lose, you'll get 'em next time!"
    elif is_p and not did_win:     scenario_msg = "You were so close to that championship, you'll win next year for sure!"
    elif did_win:                  scenario_msg = "You smoked 'em!"
    if scenario_msg:
        final_line += f" {scenario_msg}"
    st.markdown(final_line)

    mean_line = f"The weekly mean was {_fmt_number(weekly_mean)} and the weekly median was {_fmt_number(weekly_median)}."
    luck_msg = None
    if teams_beat is not None:
        if did_win and teams_beat <= 4: luck_msg = "Lucky win!"
        elif (not did_win) and teams_beat <= 4: luck_msg = "Can't blame the schedule on this loss"
        elif (not did_win) and teams_beat >= 5: luck_msg = "Unlucky!"
        elif did_win and teams_beat >= 5: luck_msg = "You deserved this win!"
    if luck_msg:
        mean_line += f" {luck_msg}"
    abl_flag = _flag(_val(row, col_above_league_med, None))
    if abl_flag is not None:
        mean_line += " Your score was above the league median." if abl_flag == 1 else " Your score was below the league median."
    st.markdown(mean_line)

    proj_msg = _combo_projection_message(
        row=row, opponent=str(opponent),
        col_win=col_win, col_above_proj=col_above_proj,
        col_projected_wins=col_projected_wins, col_win_ats=col_win_ats,
        col_expected_odds=col_expected_odds, col_expected_spread=col_expected_spread,
        col_margin=col_margin, col_proj_score_err=col_proj_score_err, col_abs_proj_score_err=col_abs_proj_err,
    )
    if proj_msg:
        st.markdown(proj_msg)

    st.markdown(
        f"So far your record is {wins_to_date if wins_to_date is not None else 'N/A'} - "
        f"{losses_to_date if losses_to_date is not None else 'N/A'} and you would be the "
        f"{seed_to_date if seed_to_date is not None else 'N/A'} seed in the playoffs if the season ended today."
    )
    st.markdown(
        f"Based on current projections you are expected to finish the season with a projected final seed of "
        f"{_fmt_number(avg_seed)}, a {_fmt_percent(p_playoffs)} chance of making the postseason, and "
        f"{_fmt_percent(p_champ)} chance of winning the championship."
    )

    st.divider()
    st.caption("Data ↓")
    if not isinstance(df_dict, dict) or not df_dict:
        st.info("No dataset available.")
        return
    dfs: Dict[str, pd.DataFrame] = {}
    for k, v in df_dict.items():
        df2 = _as_dataframe(v)
        if df2 is not None:
            dfs[str(k)] = df2
    if not dfs:
        st.info("No DataFrame-like dataset found.")
        return
    if len(dfs) == 1:
        _, df_one = next(iter(dfs.items()))
        st.dataframe(df_one, use_container_width=True, hide_index=True)
        return
    selected = st.selectbox("Select dataset", options=list(dfs.keys()))
    st.dataframe(dfs[selected], use_container_width=True, hide_index=True)

