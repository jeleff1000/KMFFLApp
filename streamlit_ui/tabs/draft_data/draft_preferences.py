import streamlit as st
import pandas as pd

def display_draft_preferences(draft_data, player_df):
    st.header("Draft Preferences")

    draft_data['Year'] = draft_data['Year'].astype(str)
    draft_data['Team Manager'] = draft_data['Team Manager'].astype(str)
    player_df['season'] = player_df['season'].astype(str)

    if 'position' not in player_df.columns:
        st.error("The 'position' column is missing from player_df.")
        return

    years = sorted(draft_data['Year'].unique().tolist())
    team_managers = sorted(draft_data['Team Manager'].unique().tolist())
    team_managers = ['All'] + team_managers

    col1, col2, col3 = st.columns(3)
    with col1:
        start_year = st.selectbox("Start Year", years, index=0)
    with col2:
        end_year = st.selectbox("End Year", years, index=len(years)-1)
    with col3:
        selected_manager = st.selectbox("Select Manager", team_managers, index=0)

    selected_years = [y for y in years if start_year <= y <= end_year]

    def get_drafted_table(filtered_draft_data, table_title):
        if selected_years:
            filtered_draft_data = filtered_draft_data[filtered_draft_data['Year'].isin(selected_years)]
            player_df_filtered = player_df[player_df['playeryear'].str.contains('|'.join(selected_years))]
        else:
            player_df_filtered = player_df

        if selected_manager and selected_manager != 'All':
            filtered_draft_data = filtered_draft_data[filtered_draft_data['Team Manager'] == selected_manager]

        merged_data = filtered_draft_data.merge(
            player_df_filtered[['playeryear', 'player', 'points', 'week', 'season', 'position']],
            left_on=['Name Full', 'Year'],
            right_on=['player', 'season'],
            how='left'
        )

        merged_data = merged_data[
            (merged_data['Year'].astype(int) < 2021) & (merged_data['week'] <= 16) |
            (merged_data['Year'].astype(int) >= 2021) & (merged_data['week'] <= 17)
        ]

        aggregated_data = merged_data.groupby(['season', 'player', 'position']).agg({
            'points': 'sum',
            'Cost': 'first',
            'Pick': 'first',
            'Name Full': 'first',
            'Team Manager': 'first',
            'week': pd.Series.nunique
        }).reset_index()

        aggregated_data['PPG'] = (aggregated_data['points'] / aggregated_data['week']).round(2)
        aggregated_data['Personal Position Rank'] = (
            aggregated_data.groupby(['season', 'position', 'Team Manager'])['Cost']
            .rank(method='first', ascending=False)
            .astype(int)
            .astype(str)
        )
        aggregated_data['Personal Position Rank'] = aggregated_data['position'] + aggregated_data['Personal Position Rank']

        allowed_primary_positions = ["QB", "RB", "WR", "TE", "K", "DEF"]
        position_order = pd.CategoricalDtype(allowed_primary_positions, ordered=True)
        aggregated_data = aggregated_data[aggregated_data['position'].isin(allowed_primary_positions)]
        aggregated_data['position'] = aggregated_data['position'].astype(position_order)

        aggregated_data = aggregated_data[aggregated_data['Cost'] > 0]

        if selected_manager == 'All':
            avg_data = aggregated_data.groupby(
                ['Personal Position Rank', 'position']
            ).agg(
                Avg_Cost=('Cost', 'mean'),
                Max_Cost=('Cost', 'max'),
                Min_Cost=('Cost', 'min'),
                Median_Cost=('Cost', 'median'),
                PPG=('PPG', 'mean'),
                Times_Drafted=('Personal Position Rank', 'count')
            ).reset_index()
            avg_data['Team Manager'] = 'All'
        else:
            avg_data = aggregated_data.groupby(
                ['Personal Position Rank', 'position', 'Team Manager']
            ).agg(
                Avg_Cost=('Cost', 'mean'),
                Max_Cost=('Cost', 'max'),
                Min_Cost=('Cost', 'min'),
                Median_Cost=('Cost', 'median'),
                PPG=('PPG', 'mean'),
                Times_Drafted=('Personal Position Rank', 'count')
            ).reset_index()

        for col in ['Avg_Cost', 'Max_Cost', 'Min_Cost', 'Median_Cost', 'PPG']:
            avg_data[col] = avg_data[col].round(2)

        score_cols = ['Avg_Cost', 'PPG', 'Times_Drafted']
        avg_data = avg_data[~((avg_data[score_cols].isnull()) | (avg_data[score_cols] == 0)).all(axis=1)]

        avg_data['RankNum'] = avg_data['Personal Position Rank'].str.extract(r'(\d+)$').astype(int)
        avg_data['position'] = avg_data['position'].astype(position_order)
        avg_data = avg_data.sort_values(['position', 'RankNum'])

        columns_to_display = [
            'Personal Position Rank', 'position', 'Team Manager',
            'Avg_Cost', 'Max_Cost', 'Min_Cost', 'Median_Cost', 'PPG', 'Times_Drafted'
        ]
        st.subheader(table_title)
        st.dataframe(avg_data[columns_to_display], hide_index=True)

    def get_kept_table(filtered_draft_data, table_title):
        if selected_years:
            filtered_draft_data = filtered_draft_data[filtered_draft_data['Year'].isin(selected_years)]
            player_df_filtered = player_df[player_df['playeryear'].str.contains('|'.join(selected_years))]
        else:
            player_df_filtered = player_df

        if selected_manager and selected_manager != 'All':
            filtered_draft_data = filtered_draft_data[filtered_draft_data['Team Manager'] == selected_manager]

        merged_data = filtered_draft_data.merge(
            player_df_filtered[['playeryear', 'player', 'points', 'week', 'season', 'position']],
            left_on=['Name Full', 'Year'],
            right_on=['player', 'season'],
            how='left'
        )

        merged_data = merged_data[
            (merged_data['Year'].astype(int) < 2021) & (merged_data['week'] <= 16) |
            (merged_data['Year'].astype(int) >= 2021) & (merged_data['week'] <= 17)
            ]

        # First aggregate at player level
        player_data = merged_data.groupby(['player', 'position', 'Team Manager']).agg({
            'Cost': 'first',
            'points': 'sum',
            'week': pd.Series.nunique
        }).reset_index()
        player_data['PPG'] = (player_data['points'] / player_data['week']).round(2)

        allowed_primary_positions = ["QB", "RB", "WR", "TE", "K", "DEF"]
        position_order = pd.CategoricalDtype(allowed_primary_positions, ordered=True)
        player_data = player_data[player_data['position'].isin(allowed_primary_positions)]
        player_data['position'] = player_data['position'].astype(position_order)
        player_data = player_data[player_data['Cost'] > 0]

        # Now aggregate by position for summary stats
        if selected_manager == 'All':
            avg_data = player_data.groupby(['position']).agg(
                Avg_Cost=('Cost', 'mean'),
                Max_Cost=('Cost', 'max'),
                Min_Cost=('Cost', 'min'),
                Median_Cost=('Cost', 'median'),
                PPG=('PPG', 'mean'),
                Times_Kept=('player', 'count')
            ).reset_index()
            avg_data['Team Manager'] = 'All'
        else:
            avg_data = player_data.groupby(['position', 'Team Manager']).agg(
                Avg_Cost=('Cost', 'mean'),
                Max_Cost=('Cost', 'max'),
                Min_Cost=('Cost', 'min'),
                Median_Cost=('Cost', 'median'),
                PPG=('PPG', 'mean'),
                Times_Kept=('player', 'count')
            ).reset_index()

        for col in ['Avg_Cost', 'Max_Cost', 'Min_Cost', 'Median_Cost', 'PPG']:
            avg_data[col] = avg_data[col].round(2)

        score_cols = ['Avg_Cost', 'PPG', 'Times_Kept']
        avg_data = avg_data[~((avg_data[score_cols].isnull()) | (avg_data[score_cols] == 0)).all(axis=1)]

        avg_data['position'] = avg_data['position'].astype(position_order)
        avg_data = avg_data.sort_values(['position'])

        columns_to_display = [
            'position', 'Team Manager',
            'Avg_Cost', 'Max_Cost', 'Min_Cost', 'Median_Cost', 'PPG', 'Times_Kept'
        ]
        st.subheader(table_title)
        st.dataframe(avg_data[columns_to_display], hide_index=True)

    # Drafted Players table (Is Keeper Status != 1)
    get_drafted_table(draft_data[draft_data['Is Keeper Status'] != 1], "Drafted Players")

    # Kept Players table (Is Keeper Status == 1)
    get_kept_table(draft_data[draft_data['Is Keeper Status'] == 1], "Kept Players")