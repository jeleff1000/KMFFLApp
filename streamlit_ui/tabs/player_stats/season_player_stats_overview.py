import pandas as pd
import streamlit as st
from .season_player_subprocesses.season_player_basic_stats import get_basic_stats
from .season_player_subprocesses.season_player_advanced_stats import get_advanced_stats
from .season_player_subprocesses.season_player_matchup_stats import CombinedMatchupStatsViewer

class StreamlitSeasonPlayerDataViewer:
    def __init__(self, player_data, matchup_data):
        self.player_data = player_data
        self.matchup_data = matchup_data

    def get_unique_values(self, column, filters):
        filtered_data = self.apply_filters(filters)
        return sorted(list(filtered_data[column].unique()))

    def apply_filters(self, filters):
        filtered_data = self.player_data
        for column, values in filters.items():
            if values:  # Treat empty lists as "All"
                filtered_data = filtered_data[filtered_data[column].isin(values)]
        return filtered_data

    def display(self):
        st.title("Season Player Data Viewer")
        tabs = st.tabs(["Basic Stats", "Advanced Stats", "Matchup Stats"])

        def display_filters(tab_index, tab_name):
            selected_filters = {}

            # First row: Player search bar, Owner dropdown, and Rostered toggle
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                player_search = st.text_input("Search Player", key=f"player_search_{tab_name}_{tab_index}")
            with col2:
                owner_values = st.multiselect("Select Owner", self.get_unique_values("owner", selected_filters),
                                              key=f"owner_value_{tab_name}_{tab_index}")
            with col3:
                st.markdown("<div style='height: 2em;'></div>", unsafe_allow_html=True)
                show_rostered = st.toggle("Rostered", value=True, key=f"show_rostered_{tab_name}_{tab_index}")
            if player_search:
                selected_filters["player"] = \
                self.player_data[self.player_data['player'].str.contains(player_search, case=False)][
                    'player'].unique().tolist()
            selected_filters["owner"] = owner_values

            # Filter out players with "No Owner" if toggle is on
            if show_rostered:
                selected_filters["owner"] = [owner for owner in selected_filters["owner"] if owner != "No Owner"]
                if not selected_filters["owner"]:
                    selected_filters["owner"] = [owner for owner in self.get_unique_values("owner", selected_filters) if
                                                 owner != "No Owner"]

            # Second row: Position, Fantasy Position filters, Started toggle, and Per Game toggle
            col1, col2, col3, col4 = st.columns([1, 1, 0.5, 0.5])
            with col1:
                position_values = st.multiselect("Select Position",
                                                 self.get_unique_values("position", selected_filters),
                                                 key=f"position_value_{tab_name}_{tab_index}")
            with col2:
                fantasy_position_values = st.multiselect("Select Fantasy Position",
                                                         self.get_unique_values("fantasy position", selected_filters),
                                                         key=f"fantasy_position_value_{tab_name}_{tab_index}")
            with col3:
                st.markdown("<div style='height: 2em;'></div>", unsafe_allow_html=True)
                show_started = st.toggle("Started", value=False, key=f"show_started_{tab_name}_{tab_index}")
            with col4:
                st.markdown("<div style='height: 2em;'></div>", unsafe_allow_html=True)
                show_per_game = st.toggle("Per Game", value=False, key=f"show_per_game_{tab_name}_{tab_index}")
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

            # Third row: Team, Opponent Team, Year filters
            col1, col2, col3 = st.columns(3)
            with col1:
                team_values = st.multiselect("Select Team", self.get_unique_values("team", selected_filters),
                                             key=f"team_value_{tab_name}_{tab_index}")
            with col2:
                opponent_team_values = st.multiselect("Select Opponent Team",
                                                      self.get_unique_values("opponent_team", selected_filters),
                                                      key=f"opponent_team_value_{tab_name}_{tab_index}")
            with col3:
                year_values = st.multiselect("Select Year", self.get_unique_values("season", selected_filters),
                                             key=f"year_value_{tab_name}_{tab_index}")
            selected_filters["team"] = team_values
            selected_filters["opponent team"] = opponent_team_values
            selected_filters["season"] = year_values

            return selected_filters, show_per_game

        with tabs[0]:
            st.header("Basic Stats")
            filters, show_per_game = display_filters(tab_index=0, tab_name="BasicStats")
            filtered_data = self.apply_filters(filters)
            position = filters.get("position", ["All"])[0] if filters.get("position", ["All"]) else "All"
            basic_stats_df = get_basic_stats(filtered_data, position)
            if show_per_game:
                basic_stats_df = self.calculate_per_game_stats(basic_stats_df, filtered_data)
            st.dataframe(basic_stats_df, hide_index=True)

        with tabs[1]:
            st.header("Advanced Stats")
            filters, show_per_game = display_filters(tab_index=1, tab_name="AdvancedStats")
            filtered_data = self.apply_filters(filters)
            position = filters.get("position", ["All"])[0] if filters.get("position", ["All"]) else "All"
            advanced_stats_df = get_advanced_stats(filtered_data, position)
            if show_per_game:
                advanced_stats_df = self.calculate_per_game_stats(advanced_stats_df, filtered_data)
            st.dataframe(advanced_stats_df, hide_index=True)

        with tabs[2]:
            st.header("Matchup Stats")
            filters, show_per_game = display_filters(tab_index=2, tab_name="MatchupStats")
            filtered_data = self.apply_filters(filters)
            # Merge player_data with matchup_data to include managerweek
            if 'managerweek' in filtered_data.columns and 'ManagerWeek' in self.matchup_data.columns:
                merged_data = pd.merge(filtered_data, self.matchup_data[['ManagerWeek']], left_on='managerweek', right_on='ManagerWeek', how='left')
                viewer = CombinedMatchupStatsViewer(merged_data, self.matchup_data)
                viewer.display(prefix=f"matchup_stats_{2}", show_per_game=show_per_game)
            else:
                st.write("The 'managerweek' column is not available in the player data or 'ManagerWeek' column is not available in the matchup data.")

    def calculate_per_game_stats(self, stats_df, filtered_data):
        # Calculate the number of unique weeks where points is not 0 for each player
        unique_weeks = filtered_data[filtered_data['points'] != 0].groupby('player')['week'].nunique().reset_index()
        unique_weeks.columns = ['player', 'unique_weeks']

        # Merge the unique weeks with the stats dataframe
        stats_df = pd.merge(stats_df, unique_weeks, on='player', how='left')

        # Ensure numeric columns are converted to float before division
        numeric_columns = [col for col in stats_df.columns if
                           col not in ['player', 'team', 'season', 'owner', 'position', 'unique_weeks']]
        stats_df[numeric_columns] = stats_df[numeric_columns].apply(pd.to_numeric, errors='coerce')

        # Divide all the stats by the number of unique weeks
        for col in numeric_columns:
            stats_df[col] = stats_df[col] / stats_df['unique_weeks']

        # Round yard stats to two digits and touchdown stats to three digits
        yard_stats = ['points', 'Pass Yds', 'Rush Yds', 'Rec Yds', 'FG Yds', 'Def Yds Allow', 'team_points']
        td_stats = ['Int Pass TD', 'Rush TD', 'Rec TD', 'defensive_td']

        for col in yard_stats:
            if col in stats_df.columns:
                stats_df[col] = stats_df[col].astype(float).round(2)

        for col in td_stats:
            if col in stats_df.columns:
                stats_df[col].astype(float).round(3)

        # Drop the unique_weeks column
        stats_df = stats_df.drop(columns=['unique_weeks'])

        return stats_df