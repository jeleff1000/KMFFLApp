from __future__ import annotations
from typing import Any, Dict, Optional
import re
import html
import pandas as pd
import streamlit as st

PLAYER_POINTS_CANDIDATES = [
    "points", "Points", "weekly_points", "Week Points", "rolling_point_total"
]
FANTASY_POSITION_CANDIDATES = [
    "fantasy_position", "fantasy pos", "fantasy_position", "fantasyposition",
    "fantasy_pos", "lineup_slot", "lineup_position", "slot", "roster_slot",
    "Roster_Slot", "roster_position", "player_fantasy_position"
]
EXCLUDED_LINEUP_POSITIONS = {"IR", "BN"}

AWARD_CSS = """
<style>
.awards-row {display:flex;flex-wrap:wrap;gap:14px;margin:6px 0 18px 0;}
.awards-row.row1 .award-card,.awards-row.row2 .award-card {flex:1 1 48%;max-width:48%;}
@media (max-width:960px){
  .awards-row.row1 .award-card,.awards-row.row2 .award-card {flex:1 1 100%;max-width:100%;}
}
.award-card {position:relative;display:flex;align-items:center;gap:0.85rem;padding:10px 16px 10px 12px;
  border-radius:18px;box-shadow:0 3px 8px rgba(0,0,0,0.18);border:2px solid #334155;background:#f1f5f9;min-height:82px;overflow:hidden;}
.award-card.star {background:linear-gradient(135deg,#ecfdf5,#a7f3d0,#34d399);border-color:#059669;}
.award-card.dud {background:linear-gradient(135deg,#fef2f2,#fecaca,#f87171);border-color:#dc2626;}
.award-card.whatif {background:linear-gradient(135deg,#eef2ff,#c7d2fe,#818cf8);border-color:#6366f1;}
.award-card.improved {background:linear-gradient(135deg,#fefce8,#fde68a,#facc15);border-color:#f59e0b;}
.award-img-wrap {position:relative;width:70px;height:70px;flex-shrink:0;border-radius:50%;background:#fff;padding:6px;
  display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:0 2px 4px rgba(0,0,0,0.15);}
.award-img-wrap.star {box-shadow:0 0 0 4px #6ee7b7,0 0 0 8px #34d39933;}
.award-img-wrap.dud {box-shadow:0 0 0 4px #f87171,0 0 0 8px #dc262633;}
.award-img-wrap.whatif {box-shadow:0 0 0 4px #818cf8,0 0 0 8px #6366f133;}
.award-img-wrap.improved {box-shadow:0 0 0 4px #fbbf24,0 0 0 8px #f59e0b33;}
.award-img-wrap img {width:100%;height:100%;object-fit:cover;border-radius:50%;border:2px solid #334155;}
.award-emoji {position:absolute;right:12px;top:50%;transform:translateY(-50%);font-size:40px;line-height:1;
  filter:drop-shadow(0 2px 2px rgba(0,0,0,0.25));pointer-events:none;user-select:none;}
.award-content {display:flex;flex-direction:column;justify-content:center;min-width:0;padding-right:60px;}
.award-content h4 {margin:0 0 3px 0;font-size:0.82rem;font-weight:800;color:#1e293b;letter-spacing:.3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:360px;}
.award-content .player-name {margin:0 0 3px 0;font-size:1.12rem;font-weight:800;color:#0f172a;line-height:1.20rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:360px;}
.award-content .pts-line {font-size:0.78rem;font-weight:600;color:#374151;line-height:0.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:360px;}
.award-content .pts-line span.value {font-weight:700;color:#111827;}
.no-img {font-size:0.60rem;font-weight:600;text-align:center;color:#475569;}
</style>
"""

def _get_player_df(df_dict: Optional[Dict[Any, Any]]) -> Optional[pd.DataFrame]:
    if not isinstance(df_dict, dict):
        return None
    obj = df_dict.get("Player Data")
    if obj is None:
        for k, v in df_dict.items():
            if str(k).strip().lower() == "player data":
                obj = v
                break
    if isinstance(obj, pd.DataFrame):
        return obj
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        return pd.DataFrame(obj)
    if isinstance(obj, dict):
        try:
            return pd.DataFrame(obj)
        except Exception:
            return None
    return None

def _detect_points_col(df: pd.DataFrame) -> Optional[str]:
    for c in PLAYER_POINTS_CANDIDATES:
        if c in df.columns:
            return c
    for c in df.columns:
        if "point" in c.lower():
            return c
    return None

def _filter_manager_year(df: pd.DataFrame, manager: str, year: int) -> pd.DataFrame:
    year_col = next((c for c in ["season_year","year","Year","season","Season"] if c in df.columns), None)
    mgr_col = next((c for c in ["manager","Manager","owner","Owner","manager_name"] if c in df.columns), None)
    out = df
    if year_col:
        out = out[pd.to_numeric(out[year_col], errors="coerce") == year]
    if mgr_col:
        m = out[mgr_col].astype(str).str.lower() == str(manager).lower()
        if m.any():
            out = out[m]
    return out

def _find_manager_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["manager","Manager","manager_name","owner","Owner","owner_name","team_owner","team_manager"]:
        if c in df.columns:
            return c
    for c in df.columns:
        lc = c.lower()
        if "manager" in lc or "owner" in lc:
            return c
    return None

def _safe_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def _normalize(s: str) -> str:
    return re.sub(r"\W+", "", s.lower())

def _find_headshot_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["headshot_url","headshot","player_headshot","Headshot","Headshot_URL","image_url","player_image","Player_Headshot"]:
        if c in df.columns:
            return c
    for c in df.columns:
        if "head" in c.lower() and "shot" in c.lower():
            return c
    return None

def _find_fantasy_position_col(df: pd.DataFrame) -> Optional[str]:
    targets = {_normalize(x) for x in FANTASY_POSITION_CANDIDATES}
    for c in df.columns:
        if _normalize(c) in targets:
            return c
    for c in df.columns:
        lc = c.lower()
        if "fantasy" in lc and ("pos" in lc or "position" in lc):
            return c
    return None

def _compute_most_improved_two_week(df: pd.DataFrame,
                                    name_col: str,
                                    points_col: str) -> Optional[pd.Series]:
    if "cumulative_week" not in df.columns:
        return None
    work = df.copy()
    work["__cum__"] = pd.to_numeric(work["cumulative_week"], errors="coerce")
    work[points_col] = _safe_numeric(work[points_col])
    work = work[pd.notna(work["__cum__"]) & pd.notna(work[points_col])]
    if work.empty:
        return None
    cum_vals = sorted(work["__cum__"].unique())
    if len(cum_vals) < 2:
        return None
    cur_cum = cum_vals[-1]
    prev_cum = cum_vals[-2]
    agg = (work[[name_col, "__cum__", points_col]]
           .groupby([name_col, "__cum__"], as_index=False)[points_col].max())
    cur = agg[agg["__cum__"] == cur_cum].rename(columns={points_col: "cur_pts"})
    prev = agg[agg["__cum__"] == prev_cum].rename(columns={points_col: "prev_pts"})
    merged = pd.merge(cur, prev, on=name_col, how="inner")
    if merged.empty:
        return None
    merged["improvement"] = merged["cur_pts"] - merged["prev_pts"]
    merged = merged[merged["improvement"] > 0]
    if merged.empty:
        return None
    merged = merged.sort_values(["improvement","cur_pts",name_col], ascending=[False,False,True])
    best = merged.iloc[0]
    rep_row = work[(work[name_col] == best[name_col]) & (work["__cum__"] == cur_cum)].iloc[0].copy()
    rep_row["__improvement_delta__"] = float(best["improvement"])
    return rep_row

def _ensure_award_css() -> None:
    st.markdown(AWARD_CSS, unsafe_allow_html=True)

def _award_emoji(kind: str) -> str:
    return {"star":"🌟","dud":"💩","whatif":"🤦","improved":"📈"}.get(kind,"🏅")

def _render_award(row: Optional[pd.Series],
                  name_col: str,
                  points_col: str,
                  headshot_col: Optional[str],
                  title: str,
                  kind: str) -> str:
    if row is None:
        return ""
    name = html.escape(str(row.get(name_col, "")))
    pts_val = row.get(points_col)
    pts_txt = "—"
    if isinstance(pts_val, (int, float)) and pd.notna(pts_val):
        pts_txt = f"{pts_val:.2f} pts"
    if kind == "improved":
        delta = row.get("__improvement_delta__")
        if isinstance(delta, (int,float)) and pd.notna(delta):
            pts_txt = f"+{delta:.2f} pts" if delta >= 0 else f"{delta:.2f} pts"
    url = row.get(headshot_col) if headshot_col else None
    if url is not None and pd.notna(url):
        img_html = f'<div class="award-img-wrap {kind}"><img src="{html.escape(str(url))}" alt="{title} - {name}"></div>'
    else:
        img_html = f'<div class="award-img-wrap {kind}"><div class="no-img">No Image</div></div>'
    content_html = (
        f'<div class="award-content">'
        f'<h4>{html.escape(title)}</h4>'
        f'<div class="player-name">{name}</div>'
        f'<div class="pts-line"><span class="value">{pts_txt}</span></div>'
        f'</div>'
    )
    return f'<div class="award-card {kind}">{img_html}{content_html}<div class="award-emoji">{_award_emoji(kind)}</div></div>'

def display_player_weekly_recap(
    df_dict: Optional[Dict[Any, Any]],
    year: Optional[int],
    week: Optional[int],
    manager: Optional[str],
) -> None:
    if year is None or week is None or not manager:
        st.info("Select year, week and manager.")
        return

    player_df = _get_player_df(df_dict)
    if player_df is None or player_df.empty:
        st.warning("No player data.")
        return
    if "week" not in player_df.columns:
        st.warning("Column `week` missing.")
        return
    if "cumulative_week" not in player_df.columns:
        st.warning("Column `cumulative_week` missing (required for Most Improved).")
        return

    points_col = _detect_points_col(player_df)
    if not points_col:
        st.warning("Points column not found.")
        return
    player_df[points_col] = _safe_numeric(player_df[points_col])

    name_col = next((c for c in ["player","Player","player_name","Player_Name"] if c in player_df.columns), points_col)

    manager_col = _find_manager_col(player_df)
    year_col = next((c for c in ["season_year","year","Year","season","Season"] if c in player_df.columns), None)
    if manager_col:
        cur_mask = (pd.to_numeric(player_df["week"], errors="coerce") == week) & \
                   (player_df[manager_col].astype(str).str.lower() == str(manager).lower())
        if year_col:
            cur_mask &= (pd.to_numeric(player_df[year_col], errors="coerce") == year)
        current_names = set(player_df.loc[cur_mask, name_col].astype(str))
    else:
        current_names = set()
    improvement_pool = player_df[player_df[name_col].astype(str).isin(current_names)] if current_names else player_df.iloc[0:0]
    improved_row = _compute_most_improved_two_week(improvement_pool, name_col, points_col)

    subset = _filter_manager_year(player_df, manager, year)
    if subset.empty:
        st.info("No rows for selection.")
        return
    week_rows = subset[pd.to_numeric(subset["week"], errors="coerce") == week]
    if week_rows.empty:
        st.info(f"No rows for Week {week}.")
        return

    fantasy_pos_col = _find_fantasy_position_col(week_rows)
    headshot_col_all = _find_headshot_col(player_df)
    headshot_col_subset = _find_headshot_col(week_rows)

    eligible = week_rows.copy()
    if fantasy_pos_col and fantasy_pos_col in eligible.columns:
        eligible = eligible[~eligible[fantasy_pos_col].isin(EXCLUDED_LINEUP_POSITIONS)]
    eligible = eligible[pd.notna(eligible[points_col])]
    star_row = eligible.sort_values(points_col, ascending=False).iloc[0] if not eligible.empty else None
    dud_row = eligible.sort_values(points_col, ascending=True).iloc[0] if not eligible.empty else None

    def _is_opt(v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)) and not pd.isna(v):
            return int(v) == 1
        if isinstance(v, str):
            return v.strip().lower() in {"1","true","yes","y","t"}
        return False

    whatif_row = None
    if fantasy_pos_col and fantasy_pos_col in week_rows.columns:
        bench = week_rows[(week_rows[fantasy_pos_col] == "BN") & pd.notna(week_rows[points_col])].copy()
        opt_col = None
        for col in ["optimal_lineup", "optimal_lineup"]:
            if col in bench.columns:
                opt_col = col
                break
        if opt_col:
            bench = bench[bench[opt_col].apply(_is_opt)]
        else:
            bench = bench.iloc[0:0]
        if not bench.empty:
            whatif_row = bench.sort_values(points_col, ascending=False).iloc[0]

    st.markdown("## Weekly Awards")
    _ensure_award_css()
    star_html = _render_award(star_row, name_col, points_col, headshot_col_subset, "Star of the Week", "star")
    dud_html = _render_award(dud_row, name_col, points_col, headshot_col_subset, "Dud of the Week", "dud")
    whatif_html = _render_award(whatif_row, name_col, points_col, headshot_col_subset, "I Almost Started Him!", "whatif")
    improved_html = _render_award(improved_row, name_col, points_col, headshot_col_all, "Most Improved", "improved")

    if any([star_html, dud_html, whatif_html, improved_html]):
        if star_html or dud_html:
            st.markdown(f"<div class='awards-row row1'>{star_html}{dud_html}</div>", unsafe_allow_html=True)
        if whatif_html or improved_html:
            st.markdown(f"<div class='awards-row row2'>{whatif_html}{improved_html}</div>", unsafe_allow_html=True)
    else:
        st.info("No award candidates.")

    st.markdown("## Raw Week Rows")
    st.dataframe(week_rows, use_container_width=True)