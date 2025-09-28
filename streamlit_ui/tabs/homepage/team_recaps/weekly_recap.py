from typing import Any, Dict, Optional
import re

import pandas as pd
import streamlit as st

_UNIT_WORDS = (
    "point", "points", "win", "wins", "seed", "seeds",
    "chance", "favorite", "favorites", "spread", "margin",
    "victory", "loss", "losses", "team", "teams",
)
_ADJ_WORDS = ("extra", "total", "more", "fewer", "additional")

_RE_NUM_UNIT = re.compile(
    rf"(?<!\w)("
    rf"(?:\d{{1,3}}(?:,\d{{3}})*|\d+)(?:\.\d+)?%?"
    rf"(?:\s+(?:{'|'.join(_ADJ_WORDS)}))?"
    rf"(?:\s+(?:{'|'.join(_UNIT_WORDS)}))"
    rf")(?!\w)",
    re.IGNORECASE
)

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

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower().strip())

def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    norm_map = {_norm(c): c for c in df.columns}
    for cand in candidates:
        key = _norm(cand)
        if key in norm_map:
            return norm_map[key]
    return None

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
    win_flag = _flag(_val(row, col_win, None))
    above_flag = _flag(_val(row, col_above_proj, None))
    projwin_flag = _flag(_val(row, col_projected_wins, None))
    winats_flag = _flag(_val(row, col_win_ats, None))
    if None in (win_flag, above_flag, projwin_flag, winats_flag):
        return None

    expected_odds = _val(row, col_expected_odds, None)
    expected_odds_num = _to_float(expected_odds, None)

    expected_spread = _to_float(_val(row, col_expected_spread, None), None)
    margin = _to_float(_val(row, col_margin, None), None)
    proj_err = _to_float(_val(row, col_proj_score_err, None), None)
    abs_proj_err = _to_float(_val(row, col_abs_proj_score_err, None), None)
    if abs_proj_err is None and proj_err is not None:
        abs_proj_err = abs(proj_err)

    odds_pct = _fmt_percent(expected_odds)
    inv_odds_pct = "N/A" if expected_odds_num is None else (
        _fmt_percent(1 - expected_odds_num) if 0.0 <= expected_odds_num <= 1.0 else _fmt_percent(100 - expected_odds_num)
    )
    spread_str = _fmt_number(expected_spread) if expected_spread is not None else "N/A"
    spread_flip_str = _fmt_number(-expected_spread) if expected_spread is not None else "N/A"
    margin_pos_str = _fmt_number(abs(margin)) if margin is not None else "N/A"
    proj_err_pos_str = _fmt_number(abs(proj_err)) if proj_err is not None else "N/A"
    abs_proj_err_str = _fmt_number(abs(abs_proj_err)) if abs_proj_err is not None else "N/A"

    def b(s: str) -> str:
        return f"**{_escape_md_text(s)}**"

    def pts(value_str: str, value_num: Optional[float]) -> str:
        unit = "point" if (value_num is not None and abs(value_num) == 1) else "points"
        return f"{b(value_str)} {b(unit)}"

    chance_phrase = lambda pct: f"{b(pct)} {b('chance')}"
    favorite_phrase = lambda pct: f"{b(pct)} {b('favorite')}"

    margin_pts = pts(margin_pos_str, margin)
    proj_err_pts = pts(proj_err_pos_str, proj_err)
    abs_proj_err_pts = pts(abs_proj_err_str, abs_proj_err)

    w, a, pw, ats = win_flag, above_flag, projwin_flag, winats_flag

    if (w, a, pw, ats) == (0, 0, 0, 0):
        return (
            f"The haters said you couldn't do it and the haters were right! Shout out to the haters! "
            f"We expected you to lose, but not like this. When you saw {opponent} was a {favorite_phrase(inv_odds_pct)}, "
            f"you guys just decided to pack it in losing by {margin_pts} compared to the {pts(spread_flip_str, expected_spread)} spread going into the week. "
            f"Maybe a players-only meeting can sort out this debacle."
        )
    if (w, a, pw, ats) == (0, 0, 0, 1):
        return (
            f"{opponent} knew he could go easy on you this week and you proved him right. "
            f"Sure your {pts(margin_pos_str, margin)} loss was closer than the {pts(spread_flip_str, expected_spread)} spread going into the week, but you still lost. "
            f"You missed your personal projection by {abs_proj_err_pts}. "
            f"You lost but at least you kept it close? Not much good to take from this one. They are who you thought they were! And you let them off the hook!"
        )
    if (w, a, pw, ats) == (0, 0, 1, 0):
        return (
            f"Now I know this one hurts. You had a {chance_phrase(inv_odds_pct)} of winning this matchup going into the week and then… well I don't need to tell you what happened. "
            f"You lost by {margin_pts} when you were expected to win by {pts(spread_str, expected_spread)}. "
            f"You even missed your personal projections by {abs_proj_err_pts}. Scrap that entire gameplan because you won't make it far playing like this."
        )
    if (w, a, pw, ats) == (0, 1, 0, 0):
        return (
            f"You gave it your best but {opponent}'s best was better. "
            f"You exceeded your projected score by {proj_err_pts}. Goliath beat David this week but at least you gave it your all."
        )
    if (w, a, pw, ats) == (0, 1, 0, 1):
        return (
            f"You came out fighting this week. The projections had you losing by {pts(spread_flip_str, expected_spread)} but you got this game pretty close. "
            f"Only losing by {margin_pts}. You exceeded your projections by {proj_err_pts} just not enough to pull off the upset."
        )
    if (w, a, pw, ats) == (0, 1, 1, 0):
        return (
            f"{opponent} had something to prove this week! You deserved better. "
            f"You beat your projection by {proj_err_pts} but still lost a game where you were favored. Just remember, defense wins championships."
        )
    if (w, a, pw, ats) == (1, 0, 0, 1):
        return (
            f"Sometimes your opponent decides to help you out. You were the underdog coming into the week with a {chance_phrase(odds_pct)} of winning and "
            f"you didn't even play well! You fell short of your projected score by {abs_proj_err_pts}. Nevertheless, you still came away with the victory and that's all the really matters. Way to go!"
        )
    if (w, a, pw, ats) == (1, 0, 1, 0):
        return (
            f"The great teams can win ugly. Sure you only won by {margin_pts} compared to the {pts(spread_str, expected_spread)} margin entering the week, "
            f"but hey a win is a win!"
        )
    if (w, a, pw, ats) == (1, 0, 1, 1):
        return (
            f"Did you and {opponent} agree to take it easy on each other this week? "
            f"You missed your projected score by {abs_proj_err_pts} but still came away with the {pts(margin_pos_str, margin)} victory. Way to go!"
        )
    if (w, a, pw, ats) == (1, 1, 0, 1):
        return (
            f"Everyone doubted you but you pulled through! You won despite the oddsmakers only giving you a {chance_phrase(odds_pct)} at the beginning of the week. "
            f"You exceeded your projected score by {proj_err_pts} and stepped up for a big win!"
        )
    if (w, a, pw, ats) == (1, 1, 1, 0):
        return (
            f"{opponent} gave you everything they got but it wasn't enough to stop your boys. "
            f"Sure you only won by {margin_pts} but close only counts in horseshoes and grenades."
        )
    if (w, a, pw, ats) == (1, 1, 1, 1):
        return (
            f"You exceeded your lofty expectations! You had a {chance_phrase(odds_pct)} of winning and won by {margin_pts}, "
            f"we had you pegged for a {pts(spread_str, expected_spread)} favorite going into the week."
        )

    return None

def _escape_md_text(s: str) -> str:
    return re.sub(r"([\\`*_~\-])", r"\\\1", str(s or ""))

def _bold_parentheticals(s: str) -> str:
    def repl(m: re.Match) -> str:
        inner = _escape_md_text(m.group(1))
        return f"**{inner}**"
    return re.sub(r"\(([^()]*)\)", repl, str(s or ""))

def _bold_numbers_with_units(s: str) -> str:
    def bold_nums_segment(seg: str) -> str:
        def repl(m: re.Match) -> str:
            return f"**{_escape_md_text(m.group(1))}**"
        return _RE_NUM_UNIT.sub(repl, seg)

    text = str(s or "")
    out = []
    depth = 0
    buf = []
    for ch in text:
        if ch == "(":
            if depth == 0 and buf:
                out.append(bold_nums_segment("".join(buf)))
                buf = []
            depth += 1
            out.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            out.append(ch)
        else:
            if depth == 0:
                buf.append(ch)
            else:
                out.append(ch)
    if buf:
        out.append(bold_nums_segment("".join(buf)))
    return "".join(out)

def _apply_bolding(s: str) -> str:
    return _bold_parentheticals(_bold_numbers_with_units(s))

def display_weekly_recap(
    df_dict: Optional[Dict[Any, Any]] = None,
    *,
    year: int,
    week: int,
    manager: str,
) -> None:
    matchup_df = _get_matchup_df(df_dict)
    if matchup_df is None:
        st.info("No `Matchup Data` dataset available.")
        return

    df = matchup_df.copy()

    col_year = _find_col(df, ["year"])
    col_week = _find_col(df, ["week"])
    col_manager = _find_col(df, ["manager"])

    col_opponent = _find_col(df, ["opponent"])
    col_team_points = _find_col(df, ["team_points"])
    col_opponent_score = _find_col(df, ["opponent_score"])

    col_weekly_mean = _find_col(df, ["weekly_mean"])
    col_weekly_median = _find_col(df, ["weekly_median"])
    col_teams_beat = _find_col(df, ["teams_beat_this_week"])

    col_is_playoffs = _find_col(df, ["is_playoffs"])
    col_win = _find_col(df, ["win"])
    col_close_margin = _find_col(df, ["close_margin"])

    col_above_league_median = _find_col(df, ["above_league_median"])

    col_above_proj = _find_col(df, ["above_proj_score"])
    col_projected_wins = _find_col(df, ["proj_wins"])
    col_win_ats = _find_col(df, ["win_vs_spread"])

    col_expected_odds = _find_col(df, ["expected_odds"])
    col_expected_spread = _find_col(df, ["expected_spread"])
    col_margin = _find_col(df, ["margin"])
    col_proj_score_err = _find_col(df, ["proj_score_error"])
    col_abs_proj_score_err = _find_col(df, ["abs_proj_score_error"])

    if col_year:
        df = df[pd.to_numeric(df[col_year], errors="coerce").astype("Int64") == year]
    if col_week:
        df = df[pd.to_numeric(df[col_week], errors="coerce").astype("Int64") == week]
    if col_manager:
        df = df[df[col_manager].astype(str).str.strip() == str(manager).strip()]

    if df.empty:
        st.warning("No record found for the selected Manager, Week, and Year.")
        return

    row = df.iloc[0]

    opponent = _val(row, col_opponent, "Unknown")
    team_pts = _val(row, col_team_points, None)
    opp_pts = _val(row, col_opponent_score, None)

    weekly_mean = _val(row, col_weekly_mean, None)
    weekly_median = _val(row, col_weekly_median, None)
    teams_beat = _to_int(_val(row, col_teams_beat, None), None)

    final_line = (
        f"The final score of your matchup against {opponent} was "
        f"({_fmt_points(team_pts)} - {_fmt_points(opp_pts)})."
    )
    is_p = (_flag(_val(row, col_is_playoffs, None)) == 1)
    did_win = (_flag(_val(row, col_win, None)) == 1)
    close = (_flag(_val(row, col_close_margin, None)) == 1)

    scenario_msg = None
    if is_p and did_win and close:
        scenario_msg = "Way to win a close game in the playoffs!"
    elif is_p and did_win:
        scenario_msg = "Congrats on the easy playoff win, never in doubt!"
    elif is_p and close and not did_win:
        scenario_msg = "Lost your playoff game in a nail-biter, better luck next year!"
    elif did_win and close:
        scenario_msg = "Way to win a nail-biter!"
    elif close and not did_win:
        scenario_msg = "Tough way to lose, you'll get 'em next time!"
    elif is_p and not did_win:
        scenario_msg = "You were so close to that championship, you'll win next year for sure!"
    elif did_win:
        scenario_msg = "You smoked 'em!"
    if scenario_msg:
        final_line += f" {scenario_msg}"
    st.markdown(_apply_bolding(final_line))

    mean_line = f"The average score this week was ({_fmt_number(weekly_mean)} points)."

    luck_msg = None
    abl_flag = _flag(_val(row, col_above_league_median, None))
    if abl_flag is not None:
        if teams_beat is not None:
            tb_bold = f"**{teams_beat}**"
            unit = "team" if teams_beat == 1 else "teams"

            if teams_beat == 0:
                zero_phrase = "You would not have beaten any teams this week"
                if did_win and abl_flag == 0:
                    luck_msg = f"Lucky win! {zero_phrase} and still won!"
                elif (not did_win) and abl_flag == 0:
                    luck_msg = f"Can't blame the schedule on this loss. {zero_phrase}."
                elif (not did_win) and abl_flag == 1:
                    luck_msg = f"Unlucky! {zero_phrase} and still lost!"
                elif did_win and abl_flag == 1:
                    luck_msg = f"You deserved this win! {zero_phrase}!"
            else:
                if did_win and abl_flag == 0:
                    luck_msg = f"Lucky win! You would have only beaten {tb_bold} {unit} this week and still won!"
                elif (not did_win) and abl_flag == 0:
                    luck_msg = f"Can't blame the schedule on this loss. You would have only beaten {tb_bold} {unit} this week."
                elif (not did_win) and abl_flag == 1:
                    luck_msg = f"Unlucky! You would have beaten {tb_bold} {unit} this week and still lost!"
                elif did_win and abl_flag == 1:
                    luck_msg = f"You deserved this win! You would have beaten {tb_bold} {unit} this week!"
        else:
            if did_win and abl_flag == 0:
                luck_msg = "Lucky win! You were outscored by over half the league and still won!"
            elif (not did_win) and abl_flag == 0:
                luck_msg = "Can't blame the schedule on this loss. Most teams would have beat you this week."
            elif (not did_win) and abl_flag == 1:
                luck_msg = "Unlucky! You were better than most teams this week and still lost!"
            elif did_win and abl_flag == 1:
                luck_msg = "You deserved this win! You would have beaten over half the league this week!"

    if luck_msg:
        mean_line += f" {luck_msg}"

    st.markdown(_apply_bolding(mean_line))

    proj_msg = _combo_projection_message(
        row=row,
        opponent=str(opponent),
        col_win=col_win,
        col_above_proj=col_above_proj,
        col_projected_wins=col_projected_wins,
        col_win_ats=col_win_ats,
        col_expected_odds=col_expected_odds,
        col_expected_spread=col_expected_spread,
        col_margin=col_margin,
        col_proj_score_err=col_proj_score_err,
        col_abs_proj_score_err=col_abs_proj_score_err,
    )
    if proj_msg:
        st.markdown(_apply_bolding(proj_msg))