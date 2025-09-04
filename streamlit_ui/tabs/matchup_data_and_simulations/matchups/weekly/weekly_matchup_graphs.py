import streamlit as st
import pandas as pd
import altair as alt

class SeasonMatchupStatsViewer:
    def __init__(self, df):
        self.df = df

    def display_weekly_graphs(self, prefix="", selected_managers=None):
        st.header("Team Points by Week")
        required_cols = {'Manager', 'week', 'team_points', 'year'}
        if self.df is not None and required_cols.issubset(self.df.columns) and not self.df.empty:
            x_axis_week = st.toggle("Show Season Week on X-axis", value=False)
            x_field = 'week' if x_axis_week else 'Cumulative Week'

            df_sorted = self.df.sort_values(['year', 'week'])
            df_sorted['team_points'] = df_sorted['team_points'].round(2)

            if not x_axis_week:
                x_axis = alt.Axis(title='Cumulative Week')
            else:
                min_week = int(df_sorted['week'].min())
                max_week = int(df_sorted['week'].max())
                x_axis = alt.Axis(format='d', values=list(range(min_week, max_week + 1)), title='week')

            x_type = 'Q' if x_axis_week else 'O'

            if selected_managers:
                df_filtered = df_sorted[df_sorted['Manager'].isin(selected_managers)]
                df_filtered = df_filtered.sort_values(x_field)
                points = alt.Chart(df_filtered).mark_point(size=60).encode(
                    x=alt.X(f'{x_field}:{x_type}', axis=x_axis),
                    y=alt.Y('team_points:Q', scale=alt.Scale(domain=[50, 220])),
                    color='Manager:N'
                )
            else:
                df_sorted = df_sorted.sort_values(x_field)
                points = alt.Chart(df_sorted).mark_point(size=60).encode(
                    x=alt.X(f'{x_field}:{x_type}', axis=x_axis),
                    y=alt.Y('team_points:Q', scale=alt.Scale(domain=[50, 220])),
                    color='Manager:N'
                )

            if x_axis_week:
                # Line: average team_points per week across all years (dashed)
                week_avg = df_sorted.groupby('week')['team_points'].mean().reset_index()
                week_avg['team_points'] = week_avg['team_points'].round(2)
                avg_line = alt.Chart(week_avg).mark_line(strokeDash=[5, 5], size=5, color='black').encode(
                    x=alt.X('week:Q', axis=x_axis),
                    y=alt.Y('team_points:Q', scale=alt.Scale(domain=[50, 220]))
                )
                chart = points + avg_line
            else:
                # Cumulative average resets per year
                df_sorted['League Cumulative Avg'] = (
                    df_sorted.groupby('year')['team_points']
                    .expanding().mean().reset_index(level=0, drop=True)
                ).round(2)
                league_avg = df_sorted.groupby(['year', 'Cumulative Week']).agg({'League Cumulative Avg': 'last'}).reset_index()
                cumulative_line = alt.Chart(league_avg).mark_line(strokeDash=[5, 5], size=5, color='black').encode(
                    x=alt.X('Cumulative Week:O', axis=x_axis),
                    y=alt.Y('League Cumulative Avg:Q', scale=alt.Scale(domain=[50, 220])),
                    detail='year:N'
                )
                # Add vertical gridlines for year boundaries
                year_boundaries = df_sorted.groupby('year')['Cumulative Week'].min().reset_index()
                year_rules = alt.Chart(year_boundaries).mark_rule(color='gray', strokeDash=[2,2]).encode(
                    x=alt.X('Cumulative Week:O', axis=x_axis)
                )
                # Add year labels above gridlines
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
                chart = points + cumulative_line + year_rules + year_labels

            chart = chart.properties(width=800, height=400)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("Required columns (`Manager`, `week`, `team_points`, `year`) are missing or DataFrame is empty.")

def display_weekly_graphs(df, prefix="", selected_managers=None):
    viewer = SeasonMatchupStatsViewer(df)
    viewer.display_weekly_graphs(prefix=prefix, selected_managers=selected_managers)