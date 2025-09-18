import streamlit as st
import pandas as pd
from .matchups.weekly.weekly_matchup_overview import WeeklyMatchupDataViewer


def _select_week(base_df):
    mode = st.radio("Selection Mode", ["Today's Date", "Specific Week"], horizontal=True, key="exp_mode")
    if mode == "Today's Date":
        year = int(base_df['year'].max())
        week = int(base_df[base_df['year'] == year]['week'].max())
        st.caption(f"Auto-selected Year {year}, Week {week}")
    else:
        years = sorted(base_df['year'].astype(int).unique())
        c_week, c_year = st.columns(2)
        year_choice = c_year.selectbox("Year", ["Select Year"] + [str(y) for y in years], key="exp_year")
        if year_choice == "Select Year":
            return None, None
        year = int(year_choice)
        weeks = sorted(base_df[base_df['year'] == year]['week'].astype(int).unique())
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
    needed = ['Manager', 'Wins to Date', 'Losses to Date'] + shuffle_cols
    needed = [c for c in needed if c in week_slice.columns]
    df = (week_slice[needed]
          .drop_duplicates(subset=['Manager'])
          .set_index('Manager')
          .sort_index())
    rename_map = {c: f"{int(c.split('_')[1])}-{week - int(c.split('_')[1])}" for c in shuffle_cols}
    df = df.rename(columns=rename_map)
    if {'Wins to Date', 'Losses to Date'}.issubset(df.columns):
        df['Actual Record'] = df['Wins to Date'].astype(int).astype(str) + '-' + df['Losses to Date'].astype(int).astype(str)
        df = df.drop(columns=['Wins to Date', 'Losses to Date'])
    ordered = sorted([c for c in df.columns if c != 'Actual Record'],
                     key=lambda c: int(c.split('-')[0]) if '-' in c else 0)
    if 'Actual Record' in df.columns:
        ordered.append('Actual Record')
    df = df[ordered]
    styled = (df.style
              .background_gradient(cmap='RdYlGn', axis=1)
              .format(precision=2, na_rep=""))
    st.subheader("Expected Record (Raw Shuffle Data)")
    st.markdown("<style>.dataframe tbody tr td { font-size:8px; }</style>", unsafe_allow_html=True)
    st.dataframe(styled, use_container_width=True)


def _render_expected_seed(base_df, year, week):
    week_df = base_df[(base_df['year'] == year) & (base_df['week'] == week)]
    if week_df.empty:
        st.info("No rows for selected year/week.")
        return
    seed_cols = [c for c in week_df.columns if c.startswith("shuffle_") and c.endswith("_seed")]
    if not seed_cols:
        st.info("No shuffle seed cols.")
        return
    seed_cols = sorted(seed_cols, key=lambda c: int(c.split('_')[1]))
    cols = ['Manager'] + seed_cols
    cols = [c for c in cols if c in week_df.columns]
    df = (week_df[cols]
          .drop_duplicates(subset=['Manager'])
          .set_index('Manager')
          .sort_index())
    # Add Actual Seed from Playoff Seed to Date if present
    if 'Playoff Seed to Date' in week_df.columns:
        actual_seed = (week_df[['Manager', 'Playoff Seed to Date']]
                       .drop_duplicates(subset=['Manager'])
                       .set_index('Manager')['Playoff Seed to Date']
                       .rename('Actual Seed'))
        df = df.join(actual_seed)
    # Convert shuffle seed probabilities to numeric
    df[seed_cols] = df[seed_cols].apply(pd.to_numeric, errors='coerce')
    bye_source = [c for c in seed_cols if int(c.split('_')[1]) in (1, 2)]
    playoff_source = [c for c in seed_cols if int(c.split('_')[1]) <= 6]
    df['Bye%'] = df[bye_source].sum(axis=1).round(2) if bye_source else 0.0
    df['Playoff%'] = df[playoff_source].sum(axis=1).round(2) if playoff_source else 0.0
    # Rename shuffle_x_seed -> x
    rename_map = {c: str(int(c.split('_')[1])) for c in seed_cols}
    df = df.rename(columns=rename_map)
    iteration_cols = sorted([c for c in df.columns if c.isdigit()], key=lambda x: int(x))
    # Order columns (simulation iterations, Bye/Playoff %, Actual Seed last if present)
    ordered = iteration_cols + ['Bye%', 'Playoff%']
    if 'Actual Seed' in df.columns:
        ordered.append('Actual Seed')
        df['Actual Seed'] = pd.to_numeric(df['Actual Seed'], errors='coerce')
    df = df[ordered]
    # Rounding
    numeric_percent_cols = iteration_cols + ['Bye%', 'Playoff%']
    df[numeric_percent_cols] = df[numeric_percent_cols].round(2)
    # Styling: percent format for probability cols, raw int/float for Actual Seed
    fmt = {c: '{:.2f}%' for c in numeric_percent_cols}
    if 'Actual Seed' in df.columns:
        fmt['Actual Seed'] = '{:.0f}'
    styled = (df.style
              .background_gradient(cmap='RdYlGn', subset=iteration_cols, axis=0)
              .format(fmt))
    st.subheader("Expected Seed (Raw Shuffle Seed Data)")
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
    base_df['year'] = base_df['year'].astype(int)
    base_df['week'] = base_df['week'].astype(int)

    year, week = _select_week(base_df)
    if year is None or week is None:
        return

    _render_expected_record(base_df, year, week)
    st.markdown("---")
    _render_expected_seed(base_df, year, week)