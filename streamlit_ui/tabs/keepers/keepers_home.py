import streamlit as st
import pandas as pd
import numpy as np


class KeeperDataViewer:
    def __init__(self, player_df, draft_df, adds_df):
        required_columns = ['playeryear', 'week', 'season', 'points', 'owner', 'team', 'player', 'position', 'rolling_point_total']
        missing_columns = [col for col in required_columns if col not in player_df.columns]

        if missing_columns:
            st.error(f"Missing columns in player_df: {missing_columns}")
            st.write(f"Available columns in player_df: {player_df.columns.tolist()}")
            raise KeyError(f"Missing columns in player_df: {missing_columns}")

        self.player_df = player_df[required_columns]
        self.draft_df = draft_df[['PlayerYear', 'Cost', 'Is Keeper Status', 'Average Cost', 'Name Full', 'Year']]
        self.adds_df = adds_df[['PlayerYear', 'faab_bid']]

    @st.cache_data
    def filter_final_week_data(_self, df):
        df['season'] = df['season'].astype(int)
        return df[
            ((df['season'] >= 2014) & (df['season'] <= 2020) & (df['week'] == 16)) |
            ((df['season'] >= 2021) & (df['week'] == 17))
        ]

    @st.cache_data
    def merge_data(_self, final_week_df, draft_df, adds_df):
        draft_df['Year'] = draft_df['Year'].astype(int)
        merged_df = final_week_df.merge(draft_df, left_on='playeryear', right_on='PlayerYear', how='left')
        max_faab_df = adds_df.groupby('PlayerYear')['faab_bid'].max().reset_index()
        merged_df = merged_df.merge(max_faab_df, on='PlayerYear', how='left', suffixes=('', '_max_faab'))

        draft_df['Next Year'] = draft_df['Year'] - 1
        next_year_keeper = draft_df[draft_df['Is Keeper Status'] == 1][['Name Full', 'Next Year']]
        next_year_keeper.columns = ['Name Full', 'Year']
        next_year_keeper['Kept Next Year'] = True

        following_year_avg_cost = draft_df[['Name Full', 'Next Year', 'Average Cost']]
        following_year_avg_cost.columns = ['Name Full', 'Year', 'Avg $ Next Year']

        merged_df = merged_df.merge(next_year_keeper, on=['Name Full', 'Year'], how='left')
        merged_df = merged_df.merge(following_year_avg_cost, on=['Name Full', 'Year'], how='left')

        merged_df['Kept Next Year'] = merged_df['Kept Next Year'].fillna(False)
        merged_df['Avg $ Next Year'] = merged_df['Avg $ Next Year'].replace('-', np.nan).fillna(0).astype(float)

        return merged_df

    def display(self):
        if 'week' in self.player_df.columns and 'season' in self.player_df.columns:
            final_week_df = self.filter_final_week_data(self.player_df)
            merged_df = self.merge_data(final_week_df, self.draft_df, self.adds_df)

            merged_df = merged_df[merged_df['owner'] != 'No Owner']
            merged_df = merged_df[~merged_df['position'].isin(['DEF', 'K'])]
            merged_df['owner'] = merged_df['owner'].astype(str)

            owners = ["All"] + sorted(merged_df['owner'].unique().tolist())
            years = ["All"] + sorted(merged_df['season'].unique().tolist())

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                selected_owners = st.multiselect("Select Owner(s)", owners, default=[], key="keepers_owner_multiselect")
            with col2:
                selected_years = st.multiselect("Select Year(s)", years, default=[], key="keepers_year_multiselect")
            with col3:
                st.write("")
                go_button = st.button("Go", key="keepers_go_button")

            if go_button:
                if selected_owners and "All" not in selected_owners:
                    merged_df = merged_df[merged_df['owner'].isin(selected_owners)]
                if selected_years and "All" not in selected_years:
                    merged_df = merged_df[merged_df['season'].isin(selected_years)]

                # Set index before grouping
                self.player_df.set_index('playeryear', inplace=True)

                # Calculate Points This Year as the maximum of rolling_point_total for playeryear
                points_grouped = self.player_df['rolling_point_total'].groupby('playeryear').max()
                merged_df['Points This Year'] = merged_df['playeryear'].map(points_grouped)

                # Calculate Avg Points This Year
                def calculate_avg_points(playeryear):
                    player_data = self.player_df.loc[[playeryear]]
                    max_rolling_points = player_data['rolling_point_total'].max()
                    weeks_with_points = player_data[player_data['points'] > 0].shape[0]
                    return round(max_rolling_points / weeks_with_points, 2) if weeks_with_points > 0 else 0

                merged_df['Avg Points This Year'] = merged_df['playeryear'].map(calculate_avg_points)

                # Calculate Total Points Next Year using rolling_point_total
                def get_next_season_points(playeryear):
                    player, year = playeryear[:-2], int(playeryear[-2:])
                    next_playeryear = f"{player}{year + 1:02d}"
                    if next_playeryear in self.player_df.index:
                        next_season_points = self.player_df.loc[next_playeryear, 'rolling_point_total']
                        return next_season_points.max() if not next_season_points.empty else 0
                    return 0

                def get_next_season_avg_points(playeryear):
                    player, year = playeryear[:-2], int(playeryear[-2:])
                    next_playeryear = f"{player}{year + 1:02d}"
                    if next_playeryear in self.player_df.index:
                        next_season_points = self.player_df.loc[next_playeryear]
                        next_season_points = next_season_points[next_season_points['points'] > 0]['points']
                        return round(next_season_points.mean(), 2) if not next_season_points.empty else 0
                    return 0

                merged_df['Total Points Next Year'] = merged_df['playeryear'].map(get_next_season_points)
                merged_df['Avg Points Next Year'] = merged_df['playeryear'].map(get_next_season_avg_points)

                merged_df['Keeper Price'] = merged_df.apply(
                    lambda row: int(np.ceil(max(1, (row['Cost'] * 1.5 + 7.5) if row['Is Keeper Status'] == 1 else max(
                        row['Cost'], np.ceil(row['faab_bid'] / 2))))),
                    axis=1
                )

                merged_df['season'] = merged_df['season'].astype(str).str[-2:].astype(int)

                cost_columns = [col for col in merged_df.columns if 'Cost' in col or col == 'Keeper Price' or col == 'faab_bid']
                for col in cost_columns:
                    merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
                    if col in ['Avg $ This Year', 'Avg $ Next Year']:
                        merged_df[col] = merged_df[col].astype(float).apply(lambda x: f"${x:.2f}")
                    else:
                        merged_df[col] = merged_df[col].apply(lambda x: f"${x:.0f}")

                merged_df['Kept This Year'] = merged_df['Is Keeper Status'].apply(lambda x: True if x == 1 else False)
                merged_df = merged_df.rename(columns={
                    'owner': 'Mngr',
                    'Following Year Average Cost': 'Avg $ Next Year',
                    'Average Cost': 'Avg $ This Year',
                    'total_points_season': 'Points This Year',
                    'total_points_next_season': 'Total Points Next Year',
                    'avg_points_season': 'Avg Points This Year',
                    'avg_points_next_season': 'Avg Points Next Year'
                })

                columns_to_display = [
                    'player', 'Kept Next Year', 'Kept This Year', 'Keeper Price', 'team', 'Mngr', 'position', 'season',
                    'Avg Points This Year', 'Avg Points Next Year', 'Avg $ Next Year',
                    'Cost', 'Avg $ This Year', 'faab_bid', 'Points This Year', 'Total Points Next Year'
                ]
                merged_df = merged_df[columns_to_display]
                merged_df = merged_df.dropna(how='all', subset=columns_to_display)

                st.dataframe(merged_df, height=600, width=1200, hide_index=True)
        else:
            st.error("The required columns 'week' and 'season' are not available in the data.")