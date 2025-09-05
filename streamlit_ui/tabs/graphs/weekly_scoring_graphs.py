import streamlit as st
import pandas as pd
import altair as alt

class SeasonMatchupStatsViewer:
    def __init__(self, df):
        self.df = df

    def display_weekly_graphs(self, prefix=""):
        st.header("Team Points by Week")
        required_cols = {
            'Manager', 'week', 'team_points', 'year', 'opponent',
            'Final Playoff Seed', 'is_playoffs', 'is_consolation'
        }
        if self.df is not None and required_cols.issubset(self.df.columns) and not self.df.empty:
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

            # Multiselects in the same row, default to empty (acts as All)
            col1, col2 = st.columns(2)
            with col1:
                managers = sorted(self.df['Manager'].unique().tolist())
                selected_managers = st.multiselect(
                    "Select Manager(s)", managers, default=[], key=f"{prefix}_manager_multiselect"
                )
            with col2:
                seeds = sorted(self.df['Final Playoff Seed'].dropna().unique().tolist())
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
            if 'Cumulative Week' not in df_season_type.columns:
                df_season_type['Cumulative Week'] = df_season_type.groupby('year').cumcount() + 1

            # Multiselect filter: empty means "All"
            df_filtered = df_season_type.copy()
            if selected_managers:
                df_filtered = df_filtered[df_filtered['Manager'].isin(selected_managers)]
            if selected_seeds:
                df_filtered = df_filtered[df_filtered['Final Playoff Seed'].isin(selected_seeds)]

            x_axis_week = st.toggle("Show Season Week on X-axis", value=False)
            x_field = 'week' if x_axis_week else 'Cumulative Week'

            # Sort and round
            df_season_type = df_season_type.sort_values(['year', 'week'])
            df_season_type['team_points'] = df_season_type['team_points'].round(2)
            df_filtered = df_filtered.sort_values(['year', 'week'])
            df_filtered['team_points'] = df_filtered['team_points'].round(2)

            if not x_axis_week:
                x_axis = alt.Axis(title='Cumulative Week')
            else:
                min_week = int(df_season_type['week'].min()) if not df_season_type.empty else 1
                max_week = int(df_season_type['week'].max()) if not df_season_type.empty else 1
                x_axis = alt.Axis(format='d', values=list(range(min_week, max_week + 1)), title='week')

            x_type = 'Q' if x_axis_week else 'O'

            # Points (filtered)
            df_filtered = df_filtered.sort_values(x_field)
            points = alt.Chart(df_filtered).mark_point(size=60).encode(
                x=alt.X(f'{x_field}:{x_type}', axis=x_axis),
                y=alt.Y('team_points:Q', scale=alt.Scale(domain=[50, 220])),
                color='Manager:N'
            )

            if x_axis_week:
                # Black line: league average for season type only
                week_avg_all = df_season_type.groupby('week')['team_points'].mean().reset_index()
                week_avg_all['team_points'] = week_avg_all['team_points'].round(2)
                avg_line_all = alt.Chart(week_avg_all).mark_line(
                    strokeDash=[5, 5], size=5, color='black'
                ).encode(
                    x=alt.X('week:Q', axis=x_axis),
                    y=alt.Y('team_points:Q', scale=alt.Scale(domain=[50, 220]))
                )
                # Solid lines: filtered average per manager, colored by manager
                if selected_managers:
                    week_avg_filtered = (
                        df_filtered.groupby(['Manager', 'week'])['team_points']
                        .mean().reset_index()
                    )
                    week_avg_filtered['team_points'] = week_avg_filtered['team_points'].round(2)
                    avg_line_filtered = alt.Chart(week_avg_filtered).mark_line().encode(
                        x=alt.X('week:Q', axis=x_axis),
                        y=alt.Y('team_points:Q', scale=alt.Scale(domain=[50, 220])),
                        color='Manager:N'
                    )
                    chart = points + avg_line_all + avg_line_filtered
                else:
                    chart = points + avg_line_all
            else:
                # Black line: cumulative league average for season type only
                df_season_type['League Cumulative Avg'] = (
                    df_season_type.groupby('year')['team_points']
                    .expanding().mean().reset_index(level=0, drop=True)
                ).round(2)
                league_avg_all = df_season_type.groupby(['year', 'Cumulative Week']).agg(
                    {'League Cumulative Avg': 'last'}).reset_index()
                cumulative_line_all = alt.Chart(league_avg_all).mark_line(
                    strokeDash=[5, 5], size=5, color='black'
                ).encode(
                    x=alt.X('Cumulative Week:O', axis=x_axis),
                    y=alt.Y('League Cumulative Avg:Q', scale=alt.Scale(domain=[50, 220])),
                    detail='year:N'
                )

                # Add year boundary rules and labels
                year_boundaries = df_season_type.groupby('year')['Cumulative Week'].min().reset_index()
                year_rules = alt.Chart(year_boundaries).mark_rule(
                    color='gray', strokeDash=[2, 2]
                ).encode(
                    x=alt.X('Cumulative Week:O', axis=x_axis)
                )
                year_labels = alt.Chart(year_boundaries).mark_text(
                    dy=-225,
                    fontSize=12,
                    font='sans-serif',
                    color='black'
                ).encode(
                    x=alt.X('Cumulative Week:O'),
                    y=alt.value(220),
                    text='year:N'
                )

                # Red dashed lines: filtered cumulative average per Manager (fixed color for lines)
                if selected_managers:
                    df_filtered['Manager Cumulative Avg'] = (
                        df_filtered.groupby(['Manager', 'year'])['team_points']
                        .expanding().mean().reset_index(level=[0, 1], drop=True)
                    ).round(2)
                    manager_avg_filtered = df_filtered.groupby(['Manager', 'year', 'Cumulative Week']).agg(
                        {'Manager Cumulative Avg': 'last'}).reset_index()
                    cumulative_line_managers = alt.Chart(manager_avg_filtered).mark_line(
                        size=3  # thick, solid line
                    ).encode(
                        x=alt.X('Cumulative Week:O', axis=x_axis),
                        y=alt.Y('Manager Cumulative Avg:Q', scale=alt.Scale(domain=[50, 220])),
                        color='Manager:N',
                        detail='year:N'
                    )
                    chart = (
                            points + cumulative_line_all + cumulative_line_managers +
                            year_rules + year_labels
                    )
                else:
                    chart = (
                        points + cumulative_line_all +
                        year_rules + year_labels
                    )
            chart = chart.properties(width=800, height=400)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write(
                "Required columns (`Manager`, `week`, `team_points`, `year`, `opponent`, `Final Playoff Seed`, `is_playoffs`, `is_consolation`) are missing or DataFrame is empty."
            )

def display_weekly_scoring_graphs(df_dict, prefix=""):
    """
    Entry point for the Weekly Scoring tab.
    The `prefix` must be unique per tab instance to avoid Streamlit key collisions.
    """
    df = df_dict.get("Matchup Data")
    if df is not None:
        viewer = SeasonMatchupStatsViewer(df)
        viewer.display_weekly_graphs(prefix=prefix)
    else:
        st.write("No matchup data available.")