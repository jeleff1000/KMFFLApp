import streamlit as st
import pandas as pd
from .weekly_player_subprocesses.weekly_player_basic_stats import get_basic_stats
from .weekly_player_subprocesses.weekly_player_advanced_stats import get_advanced_stats
from .weekly_player_subprocesses.weekly_player_matchup_stats import CombinedMatchupStatsViewer

class StreamlitWeeklyPlayerDataViewer:
    def __init__(self, player_data, matchup_data):
        self.player_data = player_data
        self.matchup_data = matchup_data

    def get_unique_values(self, column, filters):
        filtered_data = self.apply_filters(filters)
        if column in filtered_data.columns:
            return sorted(list(filtered_data[column].unique()))
        else:
            return []

    def apply_filters(self, filters):
        filtered_data = self.player_data
        for column, values in filters.items():
            if values:  # Treat empty lists as "All"
                filtered_data = filtered_data[filtered_data[column].isin(values)]
        return filtered_data

    def display(self):
        st.title("Weekly Player Data Viewer")
        tabs = st.tabs(["Basic Stats", "Advanced Stats", "Matchup Stats"])

        def display_filters(tab_index):
            selected_filters = {}

            # First row: Player search bar, Owner dropdown, and Rostered toggle
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                player_search = st.text_input("Search Player", key=f"player_search_{tab_index}")
            with col2:
                owner_values = st.multiselect("Select Owner", self.get_unique_values("owner", selected_filters),
                                              key=f"owner_value_{tab_index}")
            with col3:
                st.markdown("<div style='height: 2em;'></div>", unsafe_allow_html=True)
                show_rostered = st.toggle("Rostered", value=True, key=f"show_rostered_{tab_index}")
            if player_search:
                selected_filters["player"] = [player for player in self.player_data['player'].unique() if
                                              player_search.lower() in player.lower()]
            selected_filters["owner"] = owner_values

            # Filter out players with "No Owner" if toggle is on
            if show_rostered:
                selected_filters["owner"] = [owner for owner in selected_filters["owner"] if owner != "No Owner"]
                if not selected_filters["owner"]:
                    selected_filters["owner"] = [owner for owner in self.get_unique_values("owner", selected_filters) if
                                                 owner != "No Owner"]

            # Second row: Position and Fantasy Position filters
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                position_values = st.multiselect("Select Position",
                                                 self.get_unique_values("position", selected_filters),
                                                 key=f"position_value_{tab_index}")
            with col2:
                fantasy_position_values = st.multiselect("Select Fantasy Position",
                                                         self.get_unique_values("fantasy position", selected_filters),
                                                         key=f"fantasy_position_value_{tab_index}")
            with col3:
                st.markdown("<div style='height: 2em;'></div>", unsafe_allow_html=True)
                show_started = st.toggle("Started", value=False, key=f"show_started_{tab_index}")
            selected_filters["position"] = position_values
            selected_filters["fantasy position"] = fantasy_position_values

            # Filter out players with fantasy position BN or IR if toggle is on
            if show_started:
                selected_filters["fantasy position"] = [pos for pos in selected_filters["fantasy position"] if
                                                        pos not in ["BN", "IR"]]
                if not selected_filters["fantasy position"]:
                    selected_filters["fantasy position"] = [pos for pos in
                                                            self.get_unique_values("fantasy position", selected_filters)
                                                            if pos not in ["BN", "IR"]]

            # Third row: Team, Opponent Team, Week, and Year filters
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                team_values = st.multiselect("Select Team", self.get_unique_values("team", selected_filters),
                                             key=f"team_value_{tab_index}")
            with col2:
                opponent_team_values = st.multiselect("Select Opponent Team",
                                                      self.get_unique_values("opponent_team", selected_filters),
                                                      key=f"opponent_team_value_{tab_index}")
            with col3:
                week_values = st.multiselect("Select Week", self.get_unique_values("week", selected_filters),
                                             key=f"week_value_{tab_index}")
            with col4:
                year_values = st.multiselect("Select Year", self.get_unique_values("season", selected_filters),
                                             key=f"year_value_{tab_index}")
            selected_filters["team"] = team_values
            selected_filters["opponent_team"] = opponent_team_values
            selected_filters["week"] = week_values
            selected_filters["season"] = year_values

            filtered_data = self.apply_filters(selected_filters)

            return selected_filters, filtered_data

        with tabs[0]:
            st.header("Basic Stats")
            filters, filtered_data = display_filters(tab_index=0)
            position = filters.get("position", ["All"])[0] if filters.get("position", ["All"]) else "All"
            basic_stats_df = get_basic_stats(filtered_data, position)
            st.dataframe(basic_stats_df, hide_index=True)

        with tabs[1]:
            st.header("Advanced Stats")
            filters, filtered_data = display_filters(tab_index=1)
            position = filters.get("position", ["All"])[0] if filters.get("position", ["All"]) else "All"
            advanced_stats_df = get_advanced_stats(filtered_data, position)
            st.dataframe(advanced_stats_df, hide_index=True)

        with tabs[2]:
            st.header("Matchup Stats")
            filters, filtered_data = display_filters(tab_index=2)
            # Merge player_data with matchup_data to include managerweek
            if 'managerweek' in filtered_data.columns and 'ManagerWeek' in self.matchup_data.columns:
                merged_data = pd.merge(filtered_data, self.matchup_data[['ManagerWeek']], left_on='managerweek', right_on='ManagerWeek', how='left')
                viewer = CombinedMatchupStatsViewer(merged_data, self.matchup_data)
                viewer.display(prefix=f"matchup_stats_{2}")
            else:
                st.write("The 'managerweek' column is not available in the player data or 'ManagerWeek' column is not available in the matchup data.")