import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

class StreamlitPlayerDataViewer:
    def __init__(self, df):
        self.df = df
        self.filters = []
        self.columns = [
            "team", "week", "player", "opponent_team", "owner",
            "position", "season", "fantasy_position", "Included in optimal score"
        ]
        self.columns = [col for col in self.columns if col in self.df.columns]  # Ensure columns exist in the DataFrame
        self.columns.sort()  # Ensure columns are in alphabetical order

    def display_player_data(self, df):
        if 'position' in df.columns:
            if 'QB' in df['position'].unique():
                qb_columns = [
                    'player', 'owner', 'points', 'position', 'Pass Yds', 'Int Pass TD', 'completions', 'attempts',
                    'sack_fumbles', 'sack_fumbles_lost', 'sack_yards', 'passing_2pt_conversions', 'passing_air_yards',
                    'passing_epa', 'passing_first_downs', 'passing_yards_after_catch', 'pacr', 'dakota',
                    'rushing_2pt_conversions', 'rushing_epa', 'rushing_first_downs', 'rushing_fumbles',
                    'rushing_fumbles_lost', 'Rush Att', 'Rush TD', 'Rush Yds'
                ]
                columns_order = qb_columns + [col for col in df.columns if col not in qb_columns]
            elif 'RB' in df['position'].unique():
                rb_columns = [
                    'player', 'owner', 'points', 'position', 'Rush Yds', 'Rush Att', 'Rush TD', 'Rec Yds',
                    'rushing_fumbles', 'receiving_fumbles', 'rushing_2pt_conversions', 'rushing_epa',
                    'rushing_first_downs', 'rushing_fumbles_lost', 'Rec TD', 'target_share', 'wopr', 'racr',
                    'receiving_2pt_conversions', 'receiving_air_yards', 'receiving_epa', 'receiving_first_downs',
                    'receiving_fumbles_lost', 'receiving_yards_after_catch', 'air_yards_share', 'Targets'
                ]
                columns_order = rb_columns + [col for col in df.columns if col not in rb_columns]
            else:
                columns_order = ['player', 'owner', 'points', 'position'] + [col for col in df.columns if
                                                                             col not in ['player', 'owner', 'points',
                                                                                         'position']]

        df = df[columns_order]
        df = df.sort_values(by='points', ascending=False)
        st.dataframe(df)

    def add_filter(self):
        num_columns = 3
        cols = st.columns(num_columns)
        for i in range(len(self.columns)):
            filter_column = self.columns[i]
            unique_values = ["All"] + sorted(self.df[filter_column].dropna().unique().tolist())
            filter_values = cols[i % num_columns].multiselect(f"Select {filter_column}", unique_values, default="All", key=f"filter_value_{i}")
            if "All" in filter_values:
                filter_values = unique_values[1:]  # Select all values if "All" is selected
            self.filters.append((filter_column, filter_values))

    def apply_filters(self):
        filtered_df = self.df
        for filter_column, filter_values in self.filters:
            if filter_values:
                filtered_df = filtered_df[filtered_df[filter_column].isin(filter_values)]
        return filtered_df

    def clear_filters(self):
        self.filters = []
        st.experimental_rerun()

    def visualize_data(self, df):
        if 'points' in df.columns:
            top_players = df.nlargest(10, 'points')
            plt.figure(figsize=(10, 6))
            plt.bar(top_players['player_display_name'], top_players['points'], color='skyblue')
            plt.xlabel('player_display_name')
            plt.ylabel('Points')
            plt.title('Top 10 Players by Points')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(plt)
        else:
            st.error("The 'points' column does not exist in the data")

    def display_summary(self, df):
        st.subheader("Summary Data")
        total_players = len(df)
        avg_points = df['points'].mean() if 'points' in df.columns else 0
        st.write(f"Total Players: {total_players} | Average Points: {avg_points:.2f}")

    def display(self):
        filtered_df = self.df
        self.add_filter()
        if st.button("Clear Filters"):
            self.clear_filters()
        filtered_df = self.apply_filters()
        self.display_player_data(filtered_df)
        self.display_summary(filtered_df)
        if st.button("Visualize Data"):
            self.visualize_data(filtered_df)