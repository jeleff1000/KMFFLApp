import streamlit as st
import pandas as pd
from .matchups.weekly.weekly_matchup_overview import WeeklyMatchupDataViewer

class ExpectedSeedViewer(WeeklyMatchupDataViewer):
    def __init__(self, matchup_data_df, player_data_df):
        super().__init__(matchup_data_df, player_data_df)
        self.df = matchup_data_df

    def display(self):
        st.subheader("Expected Seed (Raw Shuffle Seed Data)")
        if self.df is None or self.df.empty:
            st.write("No data available")
            return

        base_df = self.df[
            (self.df['is_playoffs'] == 0) &
            (self.df['is_consolation'] == 0)
        ].copy()
        if base_df.empty:
            st.write("No regular season data available")
            return

        base_df['year'] = base_df['year'].astype(int)
        base_df['week'] = base_df['week'].astype(int)

        mode = st.radio("Selection Mode", ["Today's Date", "Specific Week"], horizontal=True)
        if mode == "Today's Date":
            selected_year = base_df['year'].max()
            week_value = base_df[base_df['year'] == selected_year]['week'].max()
            st.caption(f"Auto-selected Year {selected_year}, Week {week_value}")
        else:
            years_sorted = sorted(base_df['year'].unique())
            col_week, col_year = st.columns(2)
            year_choice = col_year.selectbox("Year", ["Select Year"] + [str(y) for y in years_sorted])
            if year_choice == "Select Year":
                return
            selected_year = int(year_choice)
            # Fixed extra bracket here
            year_weeks = sorted(base_df[base_df['year'] == selected_year]['week'].unique())
            week_choice = col_week.selectbox("Week", ["Select Week"] + [str(w) for w in year_weeks])
            if week_choice == "Select Week":
                return
            week_value = int(week_choice)

        week_df = base_df[(base_df['year'] == selected_year) & (base_df['week'] == week_value)]
        if week_df.empty:
            st.write("No rows for selected year/week.")
            return

        seed_cols = [c for c in week_df.columns if c.startswith("shuffle_") and c.endswith("_seed")]
        if not seed_cols:
            st.write("No shuffle seed columns found.")
            return
        seed_cols = sorted(seed_cols, key=lambda c: int(c.split('_')[1]))

        cols = ['Manager'] + seed_cols
        cols = [c for c in cols if c in week_df.columns]

        display_df = (
            week_df[cols]
            .drop_duplicates(subset=['Manager'])
            .set_index('Manager')
            .sort_index()
        )

        display_df[seed_cols] = display_df[seed_cols].apply(pd.to_numeric, errors='coerce')

        bye_source = [c for c in seed_cols if int(c.split('_')[1]) in (1, 2)]
        playoff_source = [c for c in seed_cols if int(c.split('_')[1]) <= 6]

        display_df['Bye%'] = display_df[bye_source].sum(axis=1).round(2) if bye_source else 0.0
        display_df['Playoff%'] = display_df[playoff_source].sum(axis=1).round(2) if playoff_source else 0.0

        rename_map = {c: str(int(c.split('_')[1])) for c in seed_cols}
        display_df = display_df.rename(columns=rename_map)

        iteration_cols = sorted([c for c in display_df.columns if c.isdigit()], key=lambda x: int(x))
        ordered = iteration_cols + ['Bye%', 'Playoff%']
        display_df = display_df[ordered]

        numeric_cols = display_df.select_dtypes(include='number').columns
        display_df[numeric_cols] = display_df[numeric_cols].round(2)

        fmt_map = {col: '{:.2f}%' for col in ordered}

        styled = (
            display_df.style
            .background_gradient(cmap='RdYlGn', subset=iteration_cols, axis=0)
            .format(fmt_map)
        )

        st.markdown(
            """
            <style>
            .dataframe tbody tr td { font-size: 8px; }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.dataframe(styled)