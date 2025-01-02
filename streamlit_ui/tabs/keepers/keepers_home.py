import streamlit as st
import pandas as pd
import numpy as np

class KeeperDataViewer:
    def __init__(self, player_df, draft_df, adds_df):
        required_columns = ['playeryear', 'week', 'season', 'points', 'owner', 'team', 'player', 'position']
        missing_columns = [col for col in required_columns if col not in player_df.columns]

        if missing_columns:
            raise KeyError(f"Missing columns in player_df: {missing_columns}")

        self.player_df = player_df[required_columns]
        self.draft_df = draft_df[['PlayerYear', 'Cost', 'Is Keeper Status', 'Average Cost', 'Name Full', 'Year']]
        self.adds_df = adds_df[['PlayerYear', 'faab_bid']]

    @st.cache_data
    def filter_final_week_data(_self, df):
        # Convert the 'season' column to integers
        df['season'] = df['season'].astype(int)
        return df[
            ((df['season'] >= 2014) & (df['season'] <= 2020) & (df['week'] == 16)) |
            ((df['season'] >= 2021) & (df['week'] == 17))
        ]

    @st.cache_data
    def merge_data(_self, final_week_df, draft_df, adds_df):
        merged_df = final_week_df.merge(draft_df, left_on='playeryear', right_on='PlayerYear', how='left')
        max_faab_df = adds_df.groupby('PlayerYear')['faab_bid'].max().reset_index()
        merged_df = merged_df.merge(max_faab_df, on='PlayerYear', how='left', suffixes=('', '_max_faab'))

        # Add columns for next year keeper status and following year average cost
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

            # Filter out rows where owner is "No Owner"
            merged_df = merged_df[merged_df['owner'] != 'No Owner']

            # Filter out players with position "DEF" or "K"
            merged_df = merged_df[~merged_df['position'].isin(['DEF', 'K'])]

            # Convert owner column to string type
            merged_df['owner'] = merged_df['owner'].astype(str)

            # Dropdowns for owner and year
            owners = sorted(merged_df['owner'].unique().tolist())
            years = sorted(merged_df['season'].unique().tolist())

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                selected_owners = st.multiselect("Select Owner(s)", owners, key="owner_multiselect")
            with col2:
                selected_years = st.multiselect("Select Year(s)", years, key="year_multiselect")
            with col3:
                st.write("")  # Add an empty line to align the button
                go_button = st.button("Go")

            if go_button:
                # Filter based on selections
                if selected_owners:
                    merged_df = merged_df[merged_df['owner'].isin(selected_owners)]
                if selected_years:
                    merged_df = merged_df[merged_df['season'].isin(selected_years)]

                # Calculate total and average points for playeryear
                points_grouped = self.player_df.groupby(['playeryear', 'player'])['points']
                merged_df['Points This Year'] = merged_df.set_index(['playeryear', 'player']).index.map(points_grouped.sum())
                merged_df['Avg Points This Year'] = merged_df.set_index(['playeryear', 'player']).index.map(lambda x: round(points_grouped.get_group(x).loc[points_grouped.get_group(x) > 0].mean(), 2))

                # Calculate total and average points for playeryear+1
                def get_next_season_points(playeryear):
                    player, year = playeryear[:-2], int(playeryear[-2:])
                    next_playeryear = f"{player}{year + 1:02d}"
                    next_season_points = self.player_df[self.player_df['playeryear'] == next_playeryear]['points']
                    return next_season_points.sum() if not next_season_points.empty else 0

                def get_next_season_avg_points(playeryear):
                    player, year = playeryear[:-2], int(playeryear[-2:])
                    next_playeryear = f"{player}{year + 1:02d}"
                    next_season_points = self.player_df[(self.player_df['playeryear'] == next_playeryear) & (self.player_df['points'] > 0)]['points']
                    return round(next_season_points.mean(), 2) if not next_season_points.empty else 0

                merged_df['Total Points Next Year'] = merged_df['playeryear'].map(get_next_season_points)
                merged_df['Avg Points Next Year'] = merged_df['playeryear'].map(get_next_season_avg_points)

                merged_df['Keeper Price'] = merged_df.apply(
                    lambda row: np.ceil(max(1, (row['Cost'] * 1.5 + 7.5) if row['Is Keeper Status'] == 1 else max(row['Cost'], row['faab_bid'] / 2))),
                    axis=1
                ).astype(int)

                merged_df['season'] = merged_df['season'].astype(str).str[-2:].astype(int)

                # Convert cost columns to numeric before formatting
                cost_columns = [col for col in merged_df.columns if 'Cost' in col or col == 'Keeper Price' or col == 'faab_bid']
                for col in cost_columns:
                    merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
                    if col in ['Avg $ This Year', 'Avg $ Next Year']:
                        merged_df[col] = merged_df[col].astype(float).apply(lambda x: f"${x:.2f}")
                    else:
                        merged_df[col] = merged_df[col].apply(lambda x: f"${x:.0f}")

                # Convert "Is Keeper Status" to checkbox and rename columns
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

                # Remove rows with all NaN values in the columns to display
                merged_df = merged_df.dropna(how='all', subset=columns_to_display)

                st.dataframe(merged_df, height=600, width=1200, hide_index=True)
        else:
            st.error("The required columns 'week' and 'season' are not available in the data.")