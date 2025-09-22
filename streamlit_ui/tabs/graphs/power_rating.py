import streamlit as st
import pandas as pd
import altair as alt
from typing import Optional, Iterable

def _norm(s: str) -> str:
    return "".join(ch for ch in str(s).lower().strip() if ch.isalnum())

def _find_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    norm_cols = {_norm(c): c for c in df.columns}
    for cand in candidates:
        k = _norm(cand)
        if k in norm_cols:
            return norm_cols[k]
    return None

def _to_num(s, dtype=int):
    s2 = pd.to_numeric(s, errors="coerce")
    if dtype is int:
        return s2.dropna().astype(int)
    return s2

def _ensure_cumulative_week(df: pd.DataFrame, year_col: str, week_col: str) -> pd.Series:
    # Use existing column if present
    cum_col = _find_col(df, ["Cumulative Week", "cumulative_week", "cum_week"])
    if cum_col:
        return _to_num(df[cum_col], dtype=int)

    # Compute from available (year, week) pairs
    pairs = (
        df[[year_col, week_col]]
        .dropna()
        .assign(_year=_to_num(df[year_col], int), _week=_to_num(df[week_col], int))
        .dropna()
        .astype({"_year": int, "_week": int})
    )
    uniq_pairs = (
        pairs[["_year", "_week"]]
        .drop_duplicates()
        .sort_values(by=["_year", "_week"])
        .reset_index(drop=True)
    )
    uniq_pairs["cum_idx"] = range(1, len(uniq_pairs) + 1)
    mapped = pd.merge(
        pairs.reset_index()[["index", "_year", "_week"]],
        uniq_pairs,
        on=["_year", "_week"],
        how="left",
    ).set_index("index")["cum_idx"]
    return mapped.reindex(df.index)

def display_power_rating_graph(df_dict: dict, prefix: str = "graphs_manager_power_rating") -> None:
    matchup_data = df_dict.get("Matchup Data")
    if matchup_data is None or matchup_data.empty:
        st.error("Matchup data not found.")
        return

    df = matchup_data.copy()

    # Resolve columns
    year_col = _find_col(df, ["year", "season"])
    week_col = _find_col(df, ["week"])
    mgr_col = _find_col(df, ["Manager", "manager", "owner", "owner_name", "team_owner", "team_manager"])
    pr_col = _find_col(df, ["power_rating", "power rating", "power_score", "power score"])

    missing = [n for n, c in [("Year", year_col), ("Week", week_col), ("Manager", mgr_col), ("Power Rating", pr_col)] if c is None]
    if missing:
        st.info(f"Missing required columns: {', '.join(missing)}.")
        return

    # Coerce types
    df["_year"] = _to_num(df[year_col], int)
    df["_week"] = _to_num(df[week_col], int)
    df["_power"] = _to_num(df[pr_col], float)
    df["_manager"] = df[mgr_col].astype(str)

    # Compute or use Cumulative Week
    df["_cum_week"] = _ensure_cumulative_week(df, year_col, week_col)

    # Controls in a single row
    years_avail = sorted(pd.Series(df["_year"]).dropna().astype(int).unique().tolist())
    if not years_avail:
        st.info("No valid Year values.")
        return
    managers_avail = sorted(df["_manager"].dropna().unique().tolist())

    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        start_year = st.number_input(
            "Start Year",
            min_value=int(years_avail[0]),
            max_value=int(years_avail[-1]),
            value=int(years_avail[0]),
            step=1,
            key=f"{prefix}_start_year",
        )
    with c2:
        end_year = st.number_input(
            "End Year",
            min_value=int(years_avail[0]),
            max_value=int(years_avail[-1]),
            value=int(years_avail[-1]),
            step=1,
            key=f"{prefix}_end_year",
        )
    with c3:
        selected_managers = st.multiselect(
            "Manager",
            options=managers_avail,
            default=[],  # keep multiselect; empty means all
            placeholder="",
            key=f"{prefix}_managers",
        )

    # Normalize years and apply filters (empty managers == all)
    y0, y1 = (int(start_year), int(end_year))
    if y0 > y1:
        y0, y1 = y1, y0

    df_plot = df.dropna(subset=["_year", "_week", "_cum_week", "_power"]).copy()
    df_plot = df_plot[(df_plot["_year"].astype(int) >= y0) & (df_plot["_year"].astype(int) <= y1)]
    manager_filter = selected_managers if selected_managers else managers_avail
    df_plot = df_plot[df_plot["_manager"].isin(manager_filter)]

    if df_plot.empty:
        st.info("No data after applying filters.")
        return

    df_plot = df_plot.sort_values(by=["_cum_week", "_manager"])

    # Base line chart
    line_chart = (
        alt.Chart(df_plot)
        .mark_line()
        .encode(
            x=alt.X("_cum_week:Q", title="Cumulative Week"),
            y=alt.Y(
                "_power:Q",
                title="Power Rating",
                scale=alt.Scale(zero=False, nice=True),  # let y auto-scale to data
            ),
            color=alt.Color("_manager:N", title="Manager", legend=alt.Legend(columns=1)),
            tooltip=[
                alt.Tooltip("_manager:N", title="Manager"),
                alt.Tooltip("_year:Q", title="Year"),
                alt.Tooltip("_week:Q", title="Week"),
                alt.Tooltip("_cum_week:Q", title="Cumulative Week"),
                alt.Tooltip("_power:Q", title="Power Rating", format=".2f"),
            ],
        )
    )

    # Year boundary rules and top labels (computed from filtered data)
    year_boundaries = (
        df_plot.groupby("_year")["_cum_week"]
        .min()
        .reset_index()
        .rename(columns={"_cum_week": "cum_week"})
    )

    year_rules = (
        alt.Chart(year_boundaries)
        .mark_rule(color="gray", strokeDash=[2, 2])
        .encode(x=alt.X("cum_week:Q", title=None))
    )

    year_labels = (
        alt.Chart(year_boundaries)
        .mark_text(fontSize=12, font="sans-serif", color="black", baseline="top", dy=6)
        .encode(
            x=alt.X("cum_week:Q"),
            y=alt.value(-5),  # top of plotting area
            text=alt.Text("_year:N"),
        )
    )

    chart = (
        alt.layer(line_chart, year_rules, year_labels)
        .properties(height=450, width="container", title="Power Rating Over Cumulative Weeks")
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)