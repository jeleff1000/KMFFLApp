import pandas as pd
import streamlit as st

def display_season_add_drop(transaction_df, player_df, return_df=False):
    transaction_df['manager'].fillna('Unknown', inplace=True)

    # Use yahoo_position instead of position
    merged_df = pd.merge(
        transaction_df[['transaction_id', 'player_name', 'week', 'year', 'transaction_type', 'faab_bid', 'manager']],
        player_df[['player', 'week', 'year', 'rolling_point_total', 'yahoo_position']],
        left_on=['player_name', 'week', 'year'], right_on=['player', 'week', 'year'], how='left'
    )

    merged_df['manager'].fillna('Unknown', inplace=True)

    merged_df['add_points_transaction_week'] = merged_df['rolling_point_total'].where(merged_df['transaction_type'] == 'add', 0)
    merged_df['drop_points_transaction_week'] = merged_df['rolling_point_total'].where(merged_df['transaction_type'] == 'drop', 0)
    merged_df['faab_add'] = merged_df['faab_bid'].where(merged_df['transaction_type'] == 'add', 0)

    add_transactions = merged_df[merged_df['transaction_type'] == 'add']

    max_week_up_to_16 = player_df[(player_df['week'] <= 16) & (player_df['year'] <= 2020)].groupby(['player', 'year'])['week'].idxmax()
    max_week_up_to_17 = player_df[(player_df['week'] <= 17) & (player_df['year'] >= 2021)].groupby(['player', 'year'])['week'].idxmax()
    points_max_week_up_to_16 = player_df.loc[max_week_up_to_16].set_index(['player', 'year'])['rolling_point_total']
    points_max_week_up_to_17 = player_df.loc[max_week_up_to_17].set_index(['player', 'year'])['rolling_point_total']

    merged_df['points_week_max'] = merged_df.apply(
        lambda row: points_max_week_up_to_16.get((row['player_name'], row['year']), 0) if row['year'] <= 2020 else points_max_week_up_to_17.get((row['player_name'], row['year']), 0),
        axis=1
    )

    merged_df['add_points_week_max'] = merged_df['points_week_max'].where(merged_df['transaction_type'] == 'add', 0)
    merged_df['drop_points_week_max'] = merged_df['points_week_max'].where(merged_df['transaction_type'] == 'drop', 0)

    aggregated_df = merged_df.groupby(['year', 'manager']).agg({
        'faab_add': 'sum',
        'add_points_transaction_week': 'sum',
        'add_points_week_max': 'sum',
        'drop_points_transaction_week': 'sum',
        'drop_points_week_max': 'sum'
    }).reset_index()

    add_transaction_count = add_transactions.groupby(['year', 'manager']).size().reset_index(name='transaction_count')
    aggregated_df = pd.merge(aggregated_df, add_transaction_count, on=['year', 'manager'], how='left')

    aggregated_df['points_gained'] = aggregated_df['add_points_week_max'] - aggregated_df['drop_points_week_max']
    aggregated_df['year'] = aggregated_df['year'].astype(int).astype(str)

    aggregated_df.rename(columns={
        'faab_add': 'faab',
        'add_points_transaction_week': 'add_pts_to_date',
        'drop_points_transaction_week': 'drop_pts_to_date',
        'add_points_week_max': 'add_pts_ROS',
        'drop_points_week_max': 'drop_pts_ROS',
        'manager': 'manager'
    }, inplace=True)

    aggregated_df = aggregated_df[[
        'manager', 'year', 'faab', 'add_pts_to_date', 'add_pts_ROS', 'drop_pts_to_date', 'drop_pts_ROS', 'points_gained', 'transaction_count'
    ]]

    if return_df:
        return aggregated_df

    col1, col2 = st.columns(2)
    with col1:
        year_search = st.selectbox('Search by Year', options=['All'] + list(aggregated_df['year'].unique()), key='year_search_year')
    with col2:
        manager_search = st.text_input('Search by Manager', key='manager_search_year')

    if year_search and year_search != 'All':
        aggregated_df = aggregated_df[aggregated_df['year'] == year_search]
    if manager_search:
        aggregated_df = aggregated_df[aggregated_df['manager'].str.contains(manager_search, case=False, na=False)]

    st.dataframe(aggregated_df, hide_index=True)