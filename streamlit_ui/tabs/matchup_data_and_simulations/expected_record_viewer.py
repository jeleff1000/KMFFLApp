import streamlit as st
import pandas as pd
from .matchups.weekly.weekly_matchup_overview import WeeklyMatchupDataViewer

def _select_week(base_df):
    if base_df.empty or base_df['year'].dropna().empty:
        st.info("No valid year data available.")
        return None, None
    mode = st.radio("Selection Mode", ["Today's Date", "Specific Week"], horizontal=True, key="exp_mode")
    if mode == "Today's Date":
        max_year = base_df['year'].dropna().max()
        if pd.isna(max_year):
            st.info("No valid year data available.")
            return None, None
        year = int(max_year)
        week_vals = base_df[base_df['year'] == year]['week'].dropna()
        if week_vals.empty:
            st.info("No valid week data available.")
            return None, None
        week = int(week_vals.max())
        st.caption(f"Auto-selected Year {year}, Week {week}")
    else:
        years = sorted(base_df['year'].dropna().astype(int).unique())
        if not years:
            st.info("No valid year data available.")
            return None, None
        c_week, c_year = st.columns(2)
        year_choice = c_year.selectbox("Year", ["Select Year"] + [str(y) for y in years], key="exp_year")
        if year_choice == "Select Year":
            return None, None
        year = int(year_choice)
        week_vals = base_df[base_df['year'] == year]['week'].dropna()
        weeks = sorted(week_vals.astype(int).unique())
        if not weeks:
            st.info("No valid week data available.")
            return None, None
        week_choice = c_week.selectbox("Week", ["Select Week"] + [str(w) for w in weeks], key="exp_week")
        if week_choice == "Select Week":
            return None, None
        week = int(week_choice)
    return year, week

def _render_expected_record(base_df, year, week):
    week_slice = base_df[(base_df['year'] == year) & (base_df['week'] == week)]
    if week_slice.empty:
        st.info("No rows for selected year/week.")
        return
    shuffle_cols = [
        c for c in week_slice.columns
        if c.startswith("shuffle_") and c.endswith("_win") and int(c.split('_')[1]) <= week
    ]
    if not shuffle_cols:
        st.info("No shuffle win cols.")
        return
    shuffle_cols = sorted(shuffle_cols, key=lambda x: int(x.split('_')[1]))
    needed = ['manager', 'wins_to_date', 'losses_to_date'] + shuffle_cols
    needed = [c for c in needed if c in week_slice.columns]
    df = (week_slice[needed]
          .drop_duplicates(subset=['manager'])
          .set_index('manager')
          .sort_index())
    rename_map = {c: f"{int(c.split('_')[1])}-{week - int(c.split('_')[1])}" for c in shuffle_cols}
    df = df.rename(columns=rename_map)
    if {'wins_to_date', 'losses_to_date'}.issubset(df.columns):
        df['Actual Record'] = df['wins_to_date'].astype(int).astype(str) + '-' + df['losses_to_date'].astype(int).astype(str)
        df = df.drop(columns=['wins_to_date', 'losses_to_date'])
    ordered = sorted([c for c in df.columns if c != 'Actual Record'],
                     key=lambda c: int(c.split('-')[0]) if '-' in c else 0)
    if 'Actual Record' in df.columns:
        ordered.append('Actual Record')
    df = df[ordered]
    styled = (df.style
              .background_gradient(cmap='RdYlGn', axis=1)
              .format(precision=2, na_rep=""))
    st.subheader("Expected Record")
    st.markdown("<style>.dataframe tbody tr td { font-size:8px; }</style>", unsafe_allow_html=True)
    st.dataframe(styled, use_container_width=True)

def _render_expected_seed(base_df, year, week):
    week_df = base_df[(base_df['year'] == year) & (base_df['week'] == week)]
    if week_df.empty:
        st.info("No rows for selected year/week.")
        return

    raw_seed_cols = [c for c in week_df.columns if c.startswith("shuffle_") and c.endswith("_seed")]
    seed_cols = []
    week_number_map = {}
    for c in raw_seed_cols:
        parts = c.split('_')
        if len(parts) >= 3:
            num_token = parts[1]
            if num_token.isdigit():
                week_number_map[c] = int(num_token)
                seed_cols.append(c)

    if not seed_cols:
        st.info("No valid shuffle seed cols.")
        return

    seed_cols = sorted(seed_cols, key=lambda c: week_number_map[c])

    cols = ['manager'] + seed_cols
    cols = [c for c in cols if c in week_df.columns]
    df = (week_df[cols]
          .drop_duplicates(subset=['manager'])
          .set_index('manager')
          .sort_index())

    if 'playoff_seed_to_date' in week_df.columns:
        actual_seed = (week_df[['manager', 'playoff_seed_to_date']]
                       .drop_duplicates(subset=['manager'])
                       .set_index('manager')['playoff_seed_to_date']
                       .rename('Actual Seed'))
        df = df.join(actual_seed)

    df[seed_cols] = df[seed_cols].apply(pd.to_numeric, errors='coerce')

    bye_source = [c for c in seed_cols if week_number_map[c] in (1, 2)]
    playoff_source = [c for c in seed_cols if week_number_map[c] <= 6]

    df['Bye%'] = df[bye_source].sum(axis=1).round(2) if bye_source else 0.0
    df['Playoff%'] = df[playoff_source].sum(axis=1).round(2) if playoff_source else 0.0

    rename_map = {c: str(week_number_map[c]) for c in seed_cols}
    df = df.rename(columns=rename_map)

    iteration_cols = sorted([v for v in rename_map.values()], key=lambda x: int(x))
    ordered = iteration_cols + ['Bye%', 'Playoff%']
    if 'Actual Seed' in df.columns:
        ordered.append('Actual Seed')
        df['Actual Seed'] = pd.to_numeric(df['Actual Seed'], errors='coerce')

    df = df[ordered]

    numeric_percent_cols = iteration_cols + ['Bye%', 'Playoff%']
    df[numeric_percent_cols] = df[numeric_percent_cols].round(2)

    fmt = {c: '{:.2f}%' for c in numeric_percent_cols}
    if 'Actual Seed' in df.columns:
        fmt['Actual Seed'] = '{:.0f}'

    styled = (df.style
              .background_gradient(cmap='RdYlGn', subset=iteration_cols, axis=0)
              .format(fmt))
    st.subheader("Expected Seed")
    st.markdown("<style>.dataframe tbody tr td { font-size:8px; }</style>", unsafe_allow_html=True)
    st.dataframe(styled, use_container_width=True)

def display_expected_record_and_seed(matchup_data_df: pd.DataFrame, player_data_df: pd.DataFrame):
    if matchup_data_df is None or matchup_data_df.empty:
        st.write("No data available")
        return
    base_df = matchup_data_df[
        (matchup_data_df['is_playoffs'] == 0) &
        (matchup_data_df['is_consolation'] == 0)
    ].copy()
    if base_df.empty:
        st.write("No regular season data available")
        return

    # Clean year and week to only keep valid integers
    base_df = base_df[pd.to_numeric(base_df['year'], errors='coerce').notnull()]
    base_df = base_df[pd.to_numeric(base_df['week'], errors='coerce').notnull()]
    base_df['year'] = base_df['year'].astype(int)
    base_df['week'] = base_df['week'].astype(int)

    year, week = _select_week(base_df)
    if year is None or week is None:
        return

    _render_expected_record(base_df, year, week)
    st.markdown("---")
    _render_expected_seed(base_df, year, week)