import pandas as pd
import streamlit as st

def display_weekly_add_drop(transaction_df, player_df, injury_df):
    # Merge the dataframes for Weekly Add/Drop using outer join, selecting only necessary columns
    merged_df = pd.merge(transaction_df[['transaction_id', 'name', 'week', 'year', 'transaction_type', 'faab_bid', 'nickname']],
                         player_df[['player', 'week', 'season', 'points', 'position']],
                         left_on=['name', 'week', 'year'], right_on=['player', 'week', 'season'], how='outer')
    merged_df = pd.merge(merged_df, injury_df[['full_name', 'week', 'season', 'report_status']],
                         left_on=['name', 'week', 'year'], right_on=['full_name', 'week', 'season'], how='outer')

    # Calculate points for earlier weeks and weeks including and after the current week
    def calculate_points_earlier_weeks(row):
        player_points = player_df[(player_df['player'] == row['name']) & (player_df['season'] == row['year']) & (player_df['week'] < row['week'])]
        return player_points['points'].sum()

    def calculate_points_including_after(row):
        player_points = player_df[(player_df['player'] == row['name']) & (player_df['season'] == row['year']) & (player_df['week'] >= row['week'])]
        return player_points['points'].sum()

    merged_df['points_earlier_weeks'] = merged_df.apply(calculate_points_earlier_weeks, axis=1)
    merged_df['points_including_after'] = merged_df.apply(calculate_points_including_after, axis=1)

    # Create new columns based on transaction type
    merged_df['added_player'] = merged_df.apply(lambda row: row['name'] if row['transaction_type'] == 'add' else None, axis=1)
    merged_df['dropped_player'] = merged_df.apply(lambda row: row['name'] if row['transaction_type'] == 'drop' else None, axis=1)
    merged_df['add_points_earlier_weeks'] = merged_df.apply(lambda row: row['points_earlier_weeks'] if row['transaction_type'] == 'add' else None, axis=1)
    merged_df['add_points_including_after'] = merged_df.apply(lambda row: row['points_including_after'] if row['transaction_type'] == 'add' else None, axis=1)
    merged_df['drop_points_earlier_weeks'] = merged_df.apply(lambda row: row['points_earlier_weeks'] if row['transaction_type'] == 'drop' else None, axis=1)
    merged_df['drop_points_including_after'] = merged_df.apply(lambda row: row['points_including_after'] if row['transaction_type'] == 'drop' else None, axis=1)
    merged_df['dropped_player_report_status'] = merged_df.apply(lambda row: row['report_status'] if row['transaction_type'] == 'drop' else None, axis=1)
    merged_df['added_player_position'] = merged_df.apply(lambda row: row['position'] if row['transaction_type'] == 'add' else None, axis=1)
    merged_df['dropped_player_position'] = merged_df.apply(lambda row: row['position'] if row['transaction_type'] == 'drop' else None, axis=1)

    # Group by transaction_id and aggregate the necessary columns
    aggregated_df = merged_df.groupby('transaction_id').agg({
        'nickname': 'first',
        'faab_bid': 'first',
        'week': 'first',
        'year': 'first',
        'added_player': 'first',
        'dropped_player': 'first',
        'add_points_earlier_weeks': 'first',
        'add_points_including_after': 'first',
        'drop_points_earlier_weeks': 'first',
        'drop_points_including_after': 'first',
        'dropped_player_report_status': 'first',
        'added_player_position': 'first',
        'dropped_player_position': 'first'
    }).reset_index()

    # Calculate points gained
    aggregated_df['points_gained'] = aggregated_df['add_points_including_after'] - aggregated_df['drop_points_including_after']

    # Reorder the columns
    columns_order = [
        'nickname', 'week', 'year', 'added_player', 'dropped_player', 'faab_bid',
        'added_player_position', 'add_points_earlier_weeks', 'add_points_including_after',
        'dropped_player_position', 'drop_points_earlier_weeks', 'drop_points_including_after',
        'dropped_player_report_status', 'points_gained'
    ]
    aggregated_df = aggregated_df.reindex(columns=columns_order)

    # Add search bars in rows
    col1, col2, col3 = st.columns(3)
    with col1:
        year_search = st.text_input('Search by Year', key='year_search')
    with col2:
        name_search = st.text_input('Search by Added Player Name', key='added_player_search')
    with col3:
        nickname_search = st.text_input('Search by Nickname', key='nickname_search')

    col4, col5 = st.columns(2)
    with col4:
        position_search = st.text_input('Search by Position', key='position_search')

    # Filter the DataFrame based on search inputs
    if year_search:
        aggregated_df = aggregated_df[aggregated_df['year'].str.contains(year_search)]
    if nickname_search:
        aggregated_df = aggregated_df[aggregated_df['nickname'].str.contains(nickname_search, case=False, na=False)]
    if name_search:
        aggregated_df = aggregated_df[aggregated_df['added_player'].str.contains(name_search, case=False, na=False)]
    if position_search:
        aggregated_df = aggregated_df[aggregated_df['added_player_position'].str.contains(position_search, case=False, na=False)]

    # Display the merged data in a table without the index
    st.dataframe(aggregated_df, hide_index=True)