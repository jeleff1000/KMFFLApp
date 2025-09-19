import streamlit as st
import plotly.express as px
import pandas as pd

METRIC_LABELS = {
    "p_playoffs": "Playoff Odds (%)",
    "p_bye": "Bye Odds (%)",
    "exp_final_wins": "Expected Final Wins",
    "p_semis": "Semifinal Odds (%)",
    "p_final": "Final Odds (%)",
    "p_champ": "Championship Odds (%)",
}

class PlayoffOddsCumulativeViewer:
    def __init__(self, matchup_data_df):
        self.df = matchup_data_df.copy()

    def display(self):
        st.subheader("Odds Over Time (Cumulative Week)")

        df = self.df.copy()
        if df.empty:
            st.info("No data available.")
            return

        # Use source 'Cumulative Week' column directly (fallback to 'cum_week')
        cw_col = "Cumulative Week" if "Cumulative Week" in df.columns else "cum_week"
        if cw_col not in df.columns:
            st.error("Required column 'Cumulative Week' not found in data.")
            return

        # Ensure types
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df["cum_week"] = pd.to_numeric(df[cw_col], errors="coerce").astype("Int64")
        df = df.dropna(subset=["year", "cum_week"]).copy()
        df["year"] = df["year"].astype(int)
        df["cum_week"] = df["cum_week"].astype(int)

        seasons = sorted(df["year"].unique())
        if not seasons:
            st.info("No seasons available.")
            return

        min_year, max_year = int(seasons[0]), int(seasons[-1])

        # Controls
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        start_year = col1.number_input("Start Year", min_value=min_year, max_value=max_year, value=max_year, step=1, key="start_year_input_cum")
        end_year = col2.number_input("End Year", min_value=min_year, max_value=max_year, value=max_year, step=1, key="end_year_input_cum")
        metric = col3.selectbox("Metric", list(METRIC_LABELS.keys()), format_func=lambda k: METRIC_LABELS[k], key="metric_select_cum")
        go_clicked = col4.button("Go", key="go_graph_cum")

        min_cw, max_cw = int(df["cum_week"].min()), int(df["cum_week"].max())
        wcol1, wcol2 = st.columns([1, 1])
        start_cw = wcol1.number_input("Start Cumulative Week", min_value=min_cw, max_value=max_cw, value=min_cw, step=1, key="start_week_input_cum")
        end_cw = wcol2.number_input("End Cumulative Week", min_value=min_cw, max_value=max_cw, value=max_cw, step=1, key="end_week_input_cum")

        if start_year > end_year:
            st.warning("Start year must be <= end year.")
            return
        if start_cw > end_cw:
            st.warning("Start cumulative week must be <= end cumulative week.")
            return

        # Session state
        if "ts_data_cum" not in st.session_state:
            st.session_state.ts_data_cum = None
            st.session_state.ts_year_range_cum = None
            st.session_state.ts_week_range_cum = None

        if go_clicked:
            timeseries = df[
                (df["year"] >= int(start_year))
                & (df["year"] <= int(end_year))
                & (df["cum_week"] >= int(start_cw))
                & (df["cum_week"] <= int(end_cw))
            ].copy()
            st.session_state.ts_data_cum = timeseries
            st.session_state.ts_year_range_cum = (int(start_year), int(end_year))
            st.session_state.ts_week_range_cum = (int(start_cw), int(end_cw))

        if st.button("Clear", key="clear_graph_cum"):
            st.session_state.ts_data_cum = None
            st.session_state.ts_year_range_cum = None
            st.session_state.ts_week_range_cum = None

        if (
            st.session_state.ts_data_cum is None
            or st.session_state.ts_year_range_cum != (int(start_year), int(end_year))
            or st.session_state.ts_week_range_cum != (int(start_cw), int(end_cw))
        ):
            st.info("Click Go to display the graph.")
            return

        timeseries = st.session_state.ts_data_cum
        if timeseries.empty:
            st.info("No data for selected filters.")
            return

        managers = sorted(timeseries["Manager"].unique())
        selected_mgrs = st.multiselect("Select Managers (leave empty for all)", managers, default=[], key="manager_select_cum")
        effective_mgrs = managers if len(selected_mgrs) == 0 else selected_mgrs

        plot_df = timeseries[timeseries["Manager"].isin(effective_mgrs)].copy()
        if plot_df.empty:
            st.info("No data for selected managers.")
            return

        # Sort to ensure monotonic drawing within each season/manager
        plot_df = plot_df.sort_values(["Manager", "year", "cum_week"], kind="mergesort").reset_index(drop=True)
        line_ids = plot_df["Manager"].astype(str) + "_" + plot_df["year"].astype(str)

        fig = px.line(
            plot_df,
            x="cum_week",
            y=metric,
            color="Manager",
            line_group=line_ids,
            markers=False,
            labels={metric: METRIC_LABELS[metric], "Manager": "Manager"},
            hover_data={"year": True, "cum_week": True},
        )
        fig.update_traces(mode="lines", connectgaps=False)

        # Remove x-axis title and vertical gridlines
        fig.update_xaxes(title_text="", showgrid=False)

        # Keep y-axis gridlines; add % suffix for percentage metrics
        if metric != "exp_final_wins":
            fig.update_yaxes(ticksuffix="%", showgrid=True, gridwidth=1, gridcolor="lightgray")
        else:
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

        fig.update_layout(title=METRIC_LABELS[metric], legend_title="Manager")

        st.plotly_chart(fig, use_container_width=True)