import streamlit as st
import pandas as pd

from .weekly_player_subprocesses.weekly_player_basic_stats import get_basic_stats
from .weekly_player_subprocesses.weekly_player_advanced_stats import get_advanced_stats
from .weekly_player_subprocesses.weekly_player_matchup_stats import CombinedMatchupStatsViewer
from .weekly_player_subprocesses.H2H import H2HViewer


class StreamlitWeeklyPlayerDataViewer:
    def __init__(self, player_data: pd.DataFrame, matchup_data: pd.DataFrame):
        self.player_data = player_data.copy()
        self.matchup_data = matchup_data.copy()

        # Normalize types we commonly filter on
        for col in ["year", "week"]:
            if col in self.player_data.columns:
                self.player_data[col] = pd.to_numeric(self.player_data[col], errors="coerce")
            if col in self.matchup_data.columns:
                self.matchup_data[col] = pd.to_numeric(self.matchup_data[col], errors="coerce")

    def get_unique_values(self, column, filters=None):
        if filters:
            filtered_data = self.apply_filters(filters)
        else:
            filtered_data = self.player_data

        if column not in filtered_data.columns:
            return []

        series = filtered_data[column].dropna()
        if column in ["year", "week"]:
            try:
                return sorted(series.astype(float).astype(int).unique().tolist())
            except Exception:
                return sorted(series.astype(str).unique().tolist())
        else:
            return sorted(series.astype(str).unique().tolist())

    def apply_filters(self, filters):
        df = self.player_data
        for column, values in (filters or {}).items():
            if values:  # empty list = "All"
                if column in df.columns:
                    # Be robust to type mixing
                    if column in ["year", "week"]:
                        df = df[df[column].astype("Int64").isin(pd.Series(values, dtype="Int64"))]
                    else:
                        df = df[df[column].astype(str).isin([str(v) for v in values])]
        return df

    def _default_year_week(self):
        """
        Returns (default_year, default_week) where default_year is the largest year present,
        and default_week is the largest week available within that default_year.
        """
        if "year" not in self.player_data.columns or "week" not in self.player_data.columns:
            return None, None
        avail = (
            self.player_data[["year", "week"]]
            .dropna()
            .astype({"year": "Int64", "week": "Int64"})
            .drop_duplicates()
        )
        if avail.empty:
            return None, None
        max_year = int(avail["year"].max())
        max_week = int(avail.loc[avail["year"] == max_year, "week"].max())
        return max_year, max_week

    def display(self):
        st.title("Weekly Player Data Viewer")
        tabs = st.tabs(["Basic Stats", "Advanced Stats", "Matchup Stats", "H2H"])

        def display_filters(tab_index):
            selected_filters = {}

            # Row 1: Player search, Manager multiselect, Rostered toggle
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                player_search = st.text_input("Search Player", key=f"player_search_{tab_index}")
            with col2:
                manager_values = st.multiselect(
                    "Select manager", self.get_unique_values("manager"),
                    key=f"manager_value_{tab_index}"
                )
            with col3:
                st.markdown("<div style='height: 2em;'></div>", unsafe_allow_html=True)
                show_rostered = st.toggle("Rostered", value=True, key=f"show_rostered_{tab_index}")

            if player_search and "player" in self.player_data.columns:
                selected_filters["player"] = [
                    p for p in self.player_data["player"].dropna().unique()
                    if player_search.lower() in str(p).lower()
                ]
            selected_filters["manager"] = manager_values

            if show_rostered:
                selected_filters["manager"] = [
                    m for m in selected_filters["manager"] if m != "No manager"
                ]
                if not selected_filters["manager"]:
                    selected_filters["manager"] = [
                        m for m in self.get_unique_values("manager") if m != "No manager"
                    ]

            # Row 2: Positions + "Started" toggle
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                nfl_position_values = st.multiselect(
                    "Select NFL Position", self.get_unique_values("nfl_position"),
                    key=f"nfl_position_value_{tab_index}"
                )
            with col2:
                fantasy_position_values = st.multiselect(
                    "Select fantasy_position", self.get_unique_values("fantasy_position"),
                    key=f"fantasy_position_value_{tab_index}"
                )
            with col3:
                st.markdown("<div style='height: 2em;'></div>", unsafe_allow_html=True)
                show_started = st.toggle("Started", value=False, key=f"show_started_{tab_index}")

            selected_filters["nfl_position"] = nfl_position_values
            selected_filters["fantasy_position"] = fantasy_position_values

            if show_started:
                selected_filters["fantasy_position"] = [
                    pos for pos in selected_filters["fantasy_position"] if pos not in ["BN", "IR"]
                ]
                if not selected_filters["fantasy_position"]:
                    selected_filters["fantasy_position"] = [
                        pos for pos in self.get_unique_values("fantasy_position") if pos not in ["BN", "IR"]
                    ]

            # Row 3: NFL Team, Opponent Team, Week, Year
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                nfl_team_values = st.multiselect(
                    "Select NFL Team", self.get_unique_values("nfl_team"),
                    key=f"nfl_team_value_{tab_index}"
                )
            with col2:
                opponent_team_values = st.multiselect(
                    "Select opponent_team", self.get_unique_values("opponent_team"),
                    key=f"opponent_team_value_{tab_index}"
                )
            with col3:
                week_values = self.get_unique_values("week")
                with_default_week = week_values
                if week_values and isinstance(week_values[0], (int, float)):
                    with_default_week = sorted(week_values)
                week_values = st.multiselect(
                    "Select Week", with_default_week, key=f"week_value_{tab_index}"
                )
            with col4:
                year_values = st.multiselect(
                    "Select Year", self.get_unique_values("year"),
                    key=f"year_value_{tab_index}"
                )

            selected_filters["nfl_team"] = nfl_team_values
            selected_filters["opponent_team"] = opponent_team_values
            selected_filters["week"] = week_values
            selected_filters["year"] = year_values

            filtered_data = self.apply_filters(selected_filters)
            return selected_filters, filtered_data

        # Basic
        with tabs[0]:
            st.header("Basic Stats")
            _, filtered = display_filters(tab_index=0)
            basic_stats_df = get_basic_stats(filtered, "All")
            st.dataframe(basic_stats_df, hide_index=True)

        # Advanced
        with tabs[1]:
            st.header("Advanced Stats")
            _, filtered = display_filters(tab_index=1)
            advanced_stats_df = get_advanced_stats(filtered)
            st.dataframe(advanced_stats_df, hide_index=True)

        # Matchup Stats
        with tabs[2]:
            st.header("Matchup Stats")
            _, filtered = display_filters(tab_index=2)
            viewer = CombinedMatchupStatsViewer(filtered, self.matchup_data)
            viewer.display(prefix="matchup_stats")

        # H2H
        with tabs[3]:
            st.header("H2H")

            default_year, default_week = self._default_year_week()

            # Pull available years/weeks where both player & matchup data exist
            if default_year is None or default_week is None:
                st.error("Could not determine default Year/Week (no data).")
                return

            # YEAR
            years_all = sorted(
                self.player_data["year"].dropna().astype(int).unique().tolist()
            )
            try:
                year_default_index = years_all.index(default_year)
            except ValueError:
                year_default_index = len(years_all) - 1

            col1, col2, col3, col4 = st.columns([1, 1, 1, 0.7])
            with col1:
                selected_year = st.selectbox(
                    "Select Year",
                    years_all,
                    index=year_default_index,
                    key="h2h_year_value"
                )

            # WEEK (based on selected year)
            weeks_for_year = sorted(
                self.player_data.loc[self.player_data["year"] == selected_year, "week"]
                .dropna().astype(int).unique().tolist()
            )
            try:
                week_default_index = weeks_for_year.index(
                    max(weeks_for_year) if selected_year == default_year else weeks_for_year[-1]
                )
            except ValueError:
                week_default_index = len(weeks_for_year) - 1

            with col2:
                selected_week = st.selectbox(
                    "Select Week",
                    weeks_for_year,
                    index=week_default_index if week_default_index >= 0 else 0,
                    key="h2h_week_value"
                )

            # MATCHUP (default "All")
            matchups = (
                self.player_data[
                    (self.player_data["year"] == selected_year) &
                    (self.player_data["week"] == selected_week)
                ]["matchup_name"].dropna().astype(str).unique().tolist()
                if "matchup_name" in self.player_data.columns else []
            )
            matchups = ["All"] + sorted(matchups)

            with col3:
                selected_matchup_name = st.selectbox(
                    "Select Matchup Name",
                    options=matchups,
                    index=0,  # default to "All"
                    key="h2h_matchup_name_value"
                )

            with col4:
                go_button = st.button("Go", key="h2h_go_button")

            if go_button:
                # Filter the working set for H2H
                base_filtered = self.player_data[
                    (self.player_data["year"] == selected_year) &
                    (self.player_data["week"] == selected_week)
                ].copy()

                # Hand off to H2HViewer
                viewer = H2HViewer(base_filtered, self.matchup_data)

                if selected_matchup_name == "All":
                    # Render league-wide optimal team for the selected year/week
                    viewer.display(prefix="h2h", mode="league_optimal")
                else:
                    # Filter to the specific matchup and render H2H
                    viewer.display(prefix="h2h", mode="h2h", matchup_name=selected_matchup_name)
            else:
                st.caption("Select Year/Week/Matchup and click **Go** to render.")
