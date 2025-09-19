import streamlit as st
import pandas as pd
import plotly.express as px

METRIC_LABELS = {
    "p_playoffs": "Playoff Odds (%)",
    "p_bye": "Bye Odds (%)",
    "exp_final_wins": "Expected Final Wins",
    "p_semis": "Semifinal Odds (%)",
    "p_final": "Final Odds (%)",
    "p_champ": "Championship Odds (%)",
}

class PlayoffOddsViewer:
    def __init__(self, matchup_data_df):
        self.df = matchup_data_df.copy()

    def display(self):
        st.subheader("Odds Over Time")

        # Keep all weeks; still exclude consolation
        df = self.df[(self.df["is_consolation"] == 0)].copy()
        seasons = sorted(df["year"].unique())
        if not seasons:
            st.info("No seasons available.")
            return

        min_year, max_year = int(seasons[0]), int(seasons[-1])

        # Year range (default to current/latest season only)
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        start_year = col1.number_input(
            "Start Year",
            min_value=min_year,
            max_value=max_year,
            value=max_year,
            step=1,
            key="start_year_input",
        )
        end_year = col2.number_input(
            "End Year",
            min_value=min_year,
            max_value=max_year,
            value=max_year,
            step=1,
            key="end_year_input",
        )
        metric = col3.selectbox(
            "Metric",
            list(METRIC_LABELS.keys()),
            format_func=lambda k: METRIC_LABELS[k],
            key="metric_select",
        )
        go_clicked = col4.button("Go", key="go_graph")

        # Week range boxes (based on ALL weeks observed, including playoffs)
        min_week = int(df["week"].min())
        max_week = int(df["week"].max())

        wcol1, wcol2 = st.columns([1, 1])
        start_week = wcol1.number_input(
            "Start Week",
            min_value=min_week,
            max_value=max_week,
            value=min_week,
            step=1,
            key="start_week_input",
        )
        end_week = wcol2.number_input(
            "End Week",
            min_value=min_week,
            max_value=max_week,
            value=max_week,
            step=1,
            key="end_week_input",
        )

        if start_year > end_year:
            st.warning("Start Year must be less than or equal to End Year.")
            return
        if start_week > end_week:
            st.warning("Start Week must be less than or equal to End Week.")
            return

        if "ts_data" not in st.session_state:
            st.session_state.ts_data = None
            st.session_state.ts_year_range = None
            st.session_state.ts_week_range = None

        if go_clicked:
            timeseries = df[
                (df["year"] >= int(start_year))
                & (df["year"] <= int(end_year))
                & (df["week"] >= int(start_week))
                & (df["week"] <= int(end_week))
            ].copy()
            st.session_state.ts_data = timeseries
            st.session_state.ts_year_range = (int(start_year), int(end_year))
            st.session_state.ts_week_range = (int(start_week), int(end_week))

        # Replace Clear button with a Champions Only checkbox (default off)
        champions_only = st.checkbox(
            "Champions Only",
            value=False,
            key="champions_only_checkbox",
            help="Show only rows where Champion == 1",
        )

        if (
            st.session_state.ts_data is None
            or st.session_state.ts_year_range != (int(start_year), int(end_year))
            or st.session_state.ts_week_range != (int(start_week), int(end_week))
        ):
            st.info("Click Go to display the graph.")
            return

        timeseries = st.session_state.ts_data

        # Apply champions-only filter dynamically
        if champions_only:
            timeseries = timeseries[timeseries["Champion"] == 1]

        if timeseries.empty:
            st.info("No data for selected filters.")
            return

        managers = sorted(timeseries["Manager"].unique())
        selected_mgrs = st.multiselect(
            "Select Managers (leave empty for all)",
            managers,
            default=[],
            key="manager_select",
        )
        effective_mgrs = managers if len(selected_mgrs) == 0 else selected_mgrs

        plot_df = timeseries[timeseries["Manager"].isin(effective_mgrs)].copy()
        if plot_df.empty:
            st.info("No data for selected managers.")
            return

        # Ensure clean line ordering within season
        plot_df = plot_df.sort_values(["Manager", "year", "week"], kind="mergesort")

        fig = px.line(
            plot_df,
            x="week",
            y=metric,
            color="Manager",
            line_group=plot_df["Manager"].astype(str) + "_" + plot_df["year"].astype(str),
            markers=True,
            labels={"week": "Week", metric: METRIC_LABELS[metric], "Manager": "Manager"},
            hover_data={"year": True, "week": True},
        )
        fig.update_layout(
            title=METRIC_LABELS[metric],
            legend_title="Manager",
            xaxis=dict(dtick=1),
        )
        if metric != "exp_final_wins":
            fig.update_yaxes(ticksuffix="%")

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

        st.plotly_chart(fig, use_container_width=True)