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

        df = self.df[(self.df["is_consolation"] == 0)].copy()
        seasons = sorted(df["year"].unique())
        if not seasons:
            st.info("No seasons available.")
            return

        col1, col2, col3 = st.columns([1, 1, 1])
        season = col1.selectbox("Year", seasons, index=len(seasons) - 1)
        metric = col2.selectbox(
            "Metric",
            list(METRIC_LABELS.keys()),
            format_func=lambda k: METRIC_LABELS[k]
        )
        go_clicked = col3.button("Go", key="go_graph")

        if "ts_data" not in st.session_state:
            st.session_state.ts_data = None
            st.session_state.ts_season = None

        if go_clicked:
            timeseries = df[(df["year"] == season) & (df["is_playoffs"] == 0)].copy()
            st.session_state.ts_data = timeseries
            st.session_state.ts_season = season

        clear = st.button("Clear", key="clear_graph")
        if clear:
            st.session_state.ts_data = None
            st.session_state.ts_season = None

        if st.session_state.ts_data is None or st.session_state.ts_season != season:
            st.info("Click Go to display the graph.")
            return

        timeseries = st.session_state.ts_data
        if timeseries.empty:
            st.info("No data for selected season.")
            return

        managers = sorted(timeseries["Manager"].unique())
        selected_mgrs = st.multiselect(
            "Select Managers",
            managers,
            default=managers
        )

        plot_df = timeseries[timeseries["Manager"].isin(selected_mgrs)].copy()
        if plot_df.empty:
            st.info("No data for selected managers.")
            return

        fig = px.line(
            plot_df,
            x="week",
            y=metric,
            color="Manager",
            markers=True,
            labels={"week": "Week", metric: METRIC_LABELS[metric], "Manager": "Manager"},
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