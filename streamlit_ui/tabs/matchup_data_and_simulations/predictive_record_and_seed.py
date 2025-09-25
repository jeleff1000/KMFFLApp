import re
import pandas as pd
import streamlit as st


def _pred_select_week(base_df: pd.DataFrame):
    mode = st.radio("Selection Mode", ["Today's Date", "Specific Week"],
                    horizontal=True, key="pred_mode")
    if mode == "Today's Date":
        year = int(base_df['year'].max())
        week = int(base_df[base_df['year'] == year]['week'].max())
        st.caption(f"Auto-selected Year {year}, Week {week}")
    else:
        years = sorted(base_df['year'].astype(int).unique())
        c_week, c_year = st.columns(2)
        year_choice = c_year.selectbox("Year", ["Select Year"] + [str(y) for y in years],
                                       key="pred_year")
        if year_choice == "Select Year":
            return None, None
        year = int(year_choice)
        weeks = sorted(base_df[base_df['year'] == year]['week'].astype(int).unique())
        week_choice = c_week.selectbox("Week", ["Select Week"] + [str(w) for w in weeks],
                                       key="pred_week")
        if week_choice == "Select Week":
            return None, None
        week = int(week_choice)
    return year, week


def _pred_render_expected_record(base_df: pd.DataFrame, year: int, week: int):
    week_slice = base_df[(base_df['year'] == year) & (base_df['week'] == week)]
    if week_slice.empty:
        st.info("No rows for selected year/week.")
        return

    # Collect all x<number>_win columns
    win_meta = []
    for c in week_slice.columns:
        m = re.fullmatch(r"x(\d+)_win", c)
        if m:
            win_meta.append((int(m.group(1)), c))

    if not win_meta:
        st.info("No predictive win columns.")
        return

    season_len = max(k for k, _ in win_meta)

    # Sort descending by wins so records display 14-0, 13-1, ...
    win_meta.sort(key=lambda t: t[0], reverse=True)
    ordered_win_cols = [c for _, c in win_meta]

    needed = ['Manager'] + ordered_win_cols
    needed = [c for c in needed if c in week_slice.columns]

    df = (week_slice[needed]
          .drop_duplicates(subset=['Manager'])
          .set_index('Manager')
          .sort_index())

    # Rename xK_win -> K-(season_len-K)
    rename_map = {c: f"{k}-{season_len - k}" for k, c in win_meta}
    df = df.rename(columns=rename_map)

    # Order already descending by wins
    df = df[list(rename_map.values())]

    # Style
    styled = (df.style
              .background_gradient(cmap='PuBuGn', axis=1)
              .format(precision=2, na_rep=""))
    st.subheader("Predicted Record")
    st.caption(f"Season length detected: {season_len} games")
    st.markdown("<style>.dataframe tbody tr td { font-size:8px; }</style>",
                unsafe_allow_html=True)
    st.dataframe(styled, use_container_width=True)


def _pred_render_expected_seed(base_df: pd.DataFrame, year: int, week: int):
    week_df = base_df[(base_df['year'] == year) & (base_df['week'] == week)]
    if week_df.empty:
        st.info("No rows for selected year/week.")
        return

    seed_cols = []
    week_number_map = {}
    for c in week_df.columns:
        m = re.fullmatch(r"x(\d+)_seed", c)
        if m:
            num = int(m.group(1))
            week_number_map[c] = num
            seed_cols.append(c)

    if not seed_cols:
        st.info("No predictive seed columns.")
        return

    seed_cols = sorted(seed_cols, key=lambda c: week_number_map[c])

    cols = ['Manager'] + seed_cols
    cols = [c for c in cols if c in week_df.columns]
    df = (week_df[cols]
          .drop_duplicates(subset=['Manager'])
          .set_index('Manager')
          .sort_index())

    if 'Playoff Seed to Date' in week_df.columns:
        actual_seed = (week_df[['Manager', 'Playoff Seed to Date']]
                       .drop_duplicates(subset=['Manager'])
                       .set_index('Manager')['Playoff Seed to Date']
                       .rename('Actual Seed'))
        df = df.join(actual_seed)

    df[seed_cols] = df[seed_cols].apply(pd.to_numeric, errors='coerce')

    bye_source = [c for c in seed_cols if week_number_map[c] in (1, 2)]
    playoff_source = [c for c in seed_cols if week_number_map[c] <= 6]

    df['Bye%'] = df[bye_source].sum(axis=1).round(2) if bye_source else 0.0
    df['Playoff%'] = df[playoff_source].sum(axis=1).round(2) if playoff_source else 0.0

    rename_map = {c: str(week_number_map[c]) for c in seed_cols}
    df = df.rename(columns=rename_map)

    iteration_cols = sorted(rename_map.values(), key=lambda x: int(x))
    ordered = iteration_cols + ['Bye%', 'Playoff%']
    if 'Actual Seed' in df.columns:
        df['Actual Seed'] = pd.to_numeric(df['Actual Seed'], errors='coerce')
        ordered.append('Actual Seed')
    df = df[ordered]

    numeric_percent_cols = iteration_cols + ['Bye%', 'Playoff%']
    df[numeric_percent_cols] = df[numeric_percent_cols].round(2)

    fmt = {c: '{:.2f}%' for c in numeric_percent_cols}
    if 'Actual Seed' in df.columns:
        fmt['Actual Seed'] = '{:.0f}'

    styled = (df.style
              .background_gradient(cmap='PuBuGn', subset=iteration_cols, axis=0)
              .format(fmt))
    st.subheader("Predicted Seed")
    st.markdown("<style>.dataframe tbody tr td { font-size:8px; }</style>",
                unsafe_allow_html=True)
    st.dataframe(styled, use_container_width=True)


def display_predicted_record_and_seed(matchup_data_df: pd.DataFrame):
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

    year, week = _pred_select_week(base_df)
    if year is None or week is None:
        return

    _pred_render_expected_record(base_df, year, week)
    st.markdown("---")
    _pred_render_expected_seed(base_df, year, week)