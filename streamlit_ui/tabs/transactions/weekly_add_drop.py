import pandas as pd
import streamlit as st

def display_weekly_add_drop(transaction_df, player_df, keys=None, include_search_bars=True):
    transaction_df = transaction_df.drop(columns=['trader_team_key', 'tradee_team_key'], errors='ignore')

    if 'manager' not in transaction_df.columns:
        if 'nickname' in transaction_df.columns:
            transaction_df = transaction_df.rename(columns={'nickname': 'manager'})
        else:
            transaction_df['manager'] = 'Unknown'
    transaction_df['manager'].fillna('Unknown', inplace=True)

    transaction_df['year'] = transaction_df['year'].astype(int)
    player_df['year'] = player_df['year'].astype(int)

    # Use yahoo_position instead of position
    merged_df = pd.merge(
        transaction_df[['transaction_id', 'player_name', 'week', 'year', 'transaction_type', 'faab_bid', 'manager']],
        player_df[['player', 'week', 'year', 'rolling_point_total', 'yahoo_position']],
        left_on=['player_name', 'week', 'year'], right_on=['player', 'week', 'year'], how='left'
    )

    merged_df['manager'].fillna('Unknown', inplace=True)

    points_transaction_week = player_df.groupby(['player', 'year', 'week'])['rolling_point_total'].sum()
    merged_df['points_transaction_week'] = merged_df.set_index(['player_name', 'year', 'week']).index.map(
        points_transaction_week
    ).fillna(0).values

    max_week_up_to_16 = player_df[(player_df['week'] <= 16) & (player_df['year'] <= 2020)].groupby(['player', 'year'])['week'].idxmax()
    max_week_up_to_17 = player_df[(player_df['week'] <= 17) & (player_df['year'] >= 2021)].groupby(['player', 'year'])['week'].idxmax()
    points_max_week_up_to_16 = player_df.loc[max_week_up_to_16].set_index(['player', 'year'])['rolling_point_total']
    points_max_week_up_to_17 = player_df.loc[max_week_up_to_17].set_index(['player', 'year'])['rolling_point_total']

    merged_df['points_week_max'] = merged_df.apply(
        lambda row: points_max_week_up_to_16.get((row['player_name'], row['year']), 0)
        if row['year'] <= 2020 else
        points_max_week_up_to_17.get((row['player_name'], row['year']), 0),
        axis=1
    )

    merged_df['points_week_max'] = merged_df['points_week_max'] - merged_df['points_transaction_week']

    merged_df['added_player']  = merged_df['player_name'].where(merged_df['transaction_type'] == 'add')
    merged_df['dropped_player'] = merged_df['player_name'].where(merged_df['transaction_type'] == 'drop')
    merged_df['add_points_transaction_week']  = merged_df['points_transaction_week'].where(merged_df['transaction_type'] == 'add')
    merged_df['add_points_week_max']          = merged_df['points_week_max'].where(merged_df['transaction_type'] == 'add')
    merged_df['drop_points_transaction_week'] = merged_df['points_transaction_week'].where(merged_df['transaction_type'] == 'drop')
    merged_df['drop_points_week_max']         = merged_df['points_week_max'].where(merged_df['transaction_type'] == 'drop')
    merged_df['added_player_position']        = merged_df['yahoo_position'].where(merged_df['transaction_type'] == 'add')
    merged_df['dropped_player_position']      = merged_df['yahoo_position'].where(merged_df['transaction_type'] == 'drop')

    aggregated_df = merged_df.groupby('transaction_id').agg({
        'manager': 'first',
        'faab_bid': 'first',
        'week': 'first',
        'year': 'first',
        'added_player': 'first',
        'dropped_player': 'first',
        'add_points_transaction_week': 'first',
        'add_points_week_max': 'first',
        'drop_points_transaction_week': 'first',
        'drop_points_week_max': 'first',
        'added_player_position': 'first',
        'dropped_player_position': 'first'
    }).reset_index()

    aggregated_df['points_gained'] = aggregated_df['add_points_week_max'] - aggregated_df['drop_points_week_max']
    aggregated_df['year'] = aggregated_df['year'].astype(int).astype(str)

    aggregated_df.rename(columns={
        'faab_bid': 'faab',
        'added_player_position': 'add_pos',
        'dropped_player_position': 'drop_pos',
        'add_points_transaction_week': 'add_pts_to_date',
        'drop_points_transaction_week': 'drop_pts_to_date',
        'add_points_week_max': 'add_pts_ROS',
        'drop_points_week_max': 'drop_pts_ROS',
    }, inplace=True)

    aggregated_df = aggregated_df[[
        'manager', 'week', 'year', 'added_player', 'dropped_player', 'faab',
        'add_pos', 'add_pts_to_date', 'add_pts_ROS',
        'drop_pos', 'drop_pts_to_date', 'drop_pts_ROS',
        'points_gained'
    ]]

    for index, row in aggregated_df[aggregated_df['manager'] == 'Unknown'].iterrows():
        player_name = row['dropped_player']
        year = row['year']
        previous_manager = player_df[(player_df['player'] == player_name) & (player_df['year'] == int(year))]['manager']
        if not previous_manager.empty:
            aggregated_df.at[index, 'manager'] = previous_manager.iloc[0]

    if include_search_bars and keys:
        col1, col2, col3 = st.columns(3)
        with col1:
            year_search = st.selectbox('Search by Year', options=['All'] + list(aggregated_df['year'].unique()), key=keys['year_search'])
        with col2:
            name_search = st.text_input('Search by Added Player Name', key=keys['added_player_search'])
        with col3:
            nickname_search = st.text_input('Search by Manager', key=keys['nickname_search'])

        col4, col5, col6 = st.columns(3)
        with col4:
            dropped_name_search = st.text_input('Search by Dropped Player Name', key=keys['dropped_player_search'])
        with col5:
            added_position_search = st.selectbox('Search by Added Player Position', options=['All'] + list(aggregated_df['add_pos'].unique()), key=keys['added_position_search'])
        with col6:
            dropped_position_search = st.selectbox('Search by Dropped Player Position', options=['All'] + list(aggregated_df['drop_pos'].unique()), key=keys['dropped_position_search'])

        if year_search and year_search != 'All':
            aggregated_df = aggregated_df[aggregated_df['year'] == year_search]
        if nickname_search:
            aggregated_df = aggregated_df[aggregated_df['manager'].str.contains(nickname_search, case=False, na=False)]
        if name_search:
            aggregated_df = aggregated_df[aggregated_df['added_player'].str.contains(name_search, case=False, na=False)]
        if dropped_name_search:
            aggregated_df = aggregated_df[aggregated_df['dropped_player'].str.contains(dropped_name_search, case=False, na=False)]
        if added_position_search and added_position_search != 'All':
            aggregated_df = aggregated_df[aggregated_df['add_pos'] == added_position_search]
        if dropped_position_search and dropped_position_search != 'All':
            aggregated_df = aggregated_df[aggregated_df['drop_pos'] == dropped_position_search]

    st.dataframe(aggregated_df, hide_index=True)