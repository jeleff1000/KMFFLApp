import streamlit as st
import pandas as pd
import altair as alt

class AllTimeScoringStatsViewer:
    def __init__(self, df):
        self.df = df

    def display_all_time_scoring_graphs(self, prefix=""):
        st.header("All-Time Team Cumulative Points by Week")
        required_cols = {
            'manager', 'manager_week', 'team_points', 'year', 'opponent',
            'final_playoff_seed', 'is_playoffs', 'is_consolation'
        }
        if self.df is not None and required_cols.issubset(self.df.columns) and not self.df.empty:
            # Safely convert year to int, skipping invalid rows
            self.df['year'] = pd.to_numeric(self.df['year'], errors='coerce')
            self.df = self.df.dropna(subset=['year'])
            if self.df.empty:
                st.write("No valid data available for plotting after filtering year.")
                return
            self.df['year'] = self.df['year'].astype(int)
            min_year = int(self.df['year'].min())
            max_year = int(self.df['year'].max())
            col_year1, col_year2 = st.columns(2)
            with col_year1:
                start_year = st.number_input("Start Year", min_value=min_year, max_value=max_year, value=min_year, step=1, key=f"{prefix}_start_year")
            with col_year2:
                end_year = st.number_input("End Year", min_value=min_year, max_value=max_year, value=max_year, step=1, key=f"{prefix}_end_year")
            if start_year > end_year:
                st.warning("Start Year must be less than or equal to End Year.")
                return

            col1, col2 = st.columns(2)
            with col1:
                managers = sorted(self.df['manager'].unique().tolist())
                selected_managers = st.multiselect(
                    "Select Manager(s)", managers, default=[], key=f"{prefix}_manager_multiselect"
                )
            with col2:
                seeds = sorted(self.df['final_playoff_seed'].dropna().unique().tolist())
                selected_seeds = st.multiselect(
                    "Select Final Playoff Seed(s)", seeds, default=[], key=f"{prefix}_seed_multiselect"
                )

            col3, col4, col5 = st.columns(3)
            with col3:
                show_regular = st.checkbox("Regular Season", value=True, key=f"{prefix}_regular")
            with col4:
                show_playoffs = st.checkbox("Playoffs", value=True, key=f"{prefix}_playoffs")
            with col5:
                show_consolation = st.checkbox("Consolation", value=False, key=f"{prefix}_consolation")

            df_season_type = self.df.copy()
            mask_all = pd.Series([False] * len(df_season_type), index=df_season_type.index)
            if show_regular:
                mask_all |= (df_season_type['is_playoffs'] == 0) & (df_season_type['is_consolation'] == 0)
            if show_playoffs:
                mask_all |= df_season_type['is_playoffs'] == 1
            if show_consolation:
                mask_all |= df_season_type['is_consolation'] == 1
            df_season_type = df_season_type[mask_all]
            df_season_type = df_season_type[(df_season_type['year'] >= start_year) & (df_season_type['year'] <= end_year)]
            if 'cumulative_week' not in df_season_type.columns:
                df_season_type = df_season_type.sort_values(['year', 'manager_week'])
                df_season_type['cumulative_week'] = range(1, len(df_season_type) + 1)

            df_filtered = df_season_type.copy()
            if selected_managers:
                df_filtered = df_filtered[df_filtered['manager'].isin(selected_managers)]
            if selected_seeds:
                df_filtered = df_filtered[df_filtered['final_playoff_seed'].isin(selected_seeds)]

            df_filtered = df_filtered.sort_values(['manager', 'year', 'manager_week'])
            df_filtered['team_points'] = df_filtered['team_points'].round(2)

            # Cumulative points per manager
            df_filtered['manager_cumulative_points'] = (
                df_filtered.groupby('manager')['team_points'].cumsum()
            )

            # Season boundary positions (first cumulative week per year)
            year_boundaries = (
                df_season_type.groupby('year')['cumulative_week']
                .min()
                .reset_index()
            )

            # Base line chart
            base_line = alt.Chart(df_filtered).mark_line().encode(
                x=alt.X(
                    'cumulative_week:O',
                    axis=alt.Axis(title='Cumulative Week', grid=False)
                ),
                y=alt.Y(
                    'manager_cumulative_points:Q',
                    title='Cumulative Points',
                    axis=alt.Axis(grid=True),
                    scale=alt.Scale(zero=False, nice=True)
                ),
                color=alt.Color('manager:N', title='Manager'),
                tooltip=[
                    alt.Tooltip('manager:N', title='Manager'),
                    alt.Tooltip('year:Q', title='Year'),
                    alt.Tooltip('manager_week:Q', title='Week'),
                    alt.Tooltip('cumulative_week:Q', title='Cumulative Week'),
                    alt.Tooltip('manager_cumulative_points:Q', title='Cumulative Points', format='.2f')
                ]
            ).properties(width=800, height=400)

            # Dashed vertical rules at season starts
            year_rules = (
                alt.Chart(year_boundaries)
                .mark_rule(color='#bdbdbd', strokeDash=[4, 3], strokeWidth=1)
                .encode(x=alt.X('cumulative_week:O', title=None))
            )

            # Year labels at the top
            year_labels = (
                alt.Chart(year_boundaries)
                .mark_text(fontSize=12, font='sans-serif', color='black', baseline='top', dy=6)
                .encode(
                    x=alt.X('cumulative_week:O'),
                    y=alt.value(0),
                    text=alt.Text('year:N', title='Year')
                )
            )

            chart = alt.layer(year_rules, base_line, year_labels)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write(
                "Required columns (`manager`, `manager_week`, `team_points`, `year`, `opponent`, `final_playoff_seed`, `is_playoffs`, `is_consolation`) are missing or DataFrame is empty."
            )

def display_all_time_scoring_graphs(df_dict, prefix=""):
    df = df_dict.get("Matchup Data")
    if df is not None:
        viewer = AllTimeScoringStatsViewer(df)
        viewer.display_all_time_scoring_graphs(prefix=prefix)
    else:
        st.write("No matchup data available.")