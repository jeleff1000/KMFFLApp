# streamlit_ui/tabs/transactions/weekly_add_drop.py
import pandas as pd
import streamlit as st

def display_weekly_add_drop(transaction_df, player_df, keys=None, include_search_bars=True):
    # Drop unnecessary columns from transaction_df
    transaction_df = transaction_df.drop(columns=['trader_team_key', 'tradee_team_key'], errors='ignore')

    # Ensure nickname column has no missing values before merge
    transaction_df['nickname'].fillna('Unknown', inplace=True)

    # Merge the dataframes for Weekly Add/Drop using left join, selecting only necessary columns
    merged_df = pd.merge(transaction_df[['transaction_id', 'name', 'week', 'year', 'transaction_type', 'faab_bid', 'nickname']],
                         player_df[['player', 'week', 'season', 'rolling_point_total', 'position']],
                         left_on=['name', 'week', 'year'], right_on=['player', 'week', 'season'], how='left')

    # Ensure nickname column has no missing values after merge
    merged_df['nickname'].fillna('Unknown', inplace=True)

    # Calculate points for the transaction week
    points_transaction_week = player_df.set_index(['player', 'season', 'week'])['rolling_point_total']
    merged_df['points_transaction_week'] = merged_df.set_index(['name', 'year', 'week']).index.map(points_transaction_week).fillna(0).values

    # Find the maximum week up to week 17 for each player and season
    max_week_up_to_17 = player_df[player_df['week'] <= 17].groupby(['player', 'season'])['week'].idxmax()
    points_max_week_up_to_17 = player_df.loc[max_week_up_to_17].set_index(['player', 'season'])['rolling_point_total']

    # Map the points for the maximum week up to week 17
    merged_df['points_week_17'] = merged_df.set_index(['name', 'year']).index.map(points_max_week_up_to_17).fillna(0).values

    # Calculate the difference between the maximum week up to week 17 and the transaction week
    merged_df['points_week_17'] = merged_df['points_week_17'] - merged_df['points_transaction_week']

    # Create new columns based on transaction type
    merged_df['added_player'] = merged_df['name'].where(merged_df['transaction_type'] == 'add')
    merged_df['dropped_player'] = merged_df['name'].where(merged_df['transaction_type'] == 'drop')
    merged_df['add_points_transaction_week'] = merged_df['points_transaction_week'].where(merged_df['transaction_type'] == 'add')
    merged_df['add_points_week_17'] = merged_df['points_week_17'].where(merged_df['transaction_type'] == 'add')
    merged_df['drop_points_transaction_week'] = merged_df['points_transaction_week'].where(merged_df['transaction_type'] == 'drop')
    merged_df['drop_points_week_17'] = merged_df['points_week_17'].where(merged_df['transaction_type'] == 'drop')
    merged_df['added_player_position'] = merged_df['position'].where(merged_df['transaction_type'] == 'add')
    merged_df['dropped_player_position'] = merged_df['position'].where(merged_df['transaction_type'] == 'drop')

    # Group by transaction_id and aggregate the necessary columns
    aggregated_df = merged_df.groupby('transaction_id').agg({
        'nickname': 'first',
        'faab_bid': 'first',
        'week': 'first',
        'year': 'first',
        'added_player': 'first',
        'dropped_player': 'first',
        'add_points_transaction_week': 'first',
        'add_points_week_17': 'first',
        'drop_points_transaction_week': 'first',
        'drop_points_week_17': 'first',
        'added_player_position': 'first',
        'dropped_player_position': 'first'
    }).reset_index()

    # Calculate points gained
    aggregated_df['points_gained'] = aggregated_df['add_points_week_17'] - aggregated_df['drop_points_week_17']

    # Convert year to integer and then to string without formatting
    aggregated_df['year'] = aggregated_df['year'].astype(int).astype(str)

    # Rename columns
    aggregated_df.rename(columns={
        'faab_bid': 'faab',
        'added_player_position': 'add_pos',
        'dropped_player_position': 'drop_pos',
        'add_points_transaction_week': 'add_pts_to_date',
        'drop_points_transaction_week': 'drop_pts_to_date',
        'add_points_week_17': 'add_pts_ROS',
        'drop_points_week_17': 'drop_pts_ROS',
        'nickname': 'manager'
    }, inplace=True)

    # Specify the column order directly
    aggregated_df = aggregated_df[[
        'manager', 'week', 'year', 'added_player', 'dropped_player', 'faab',
        'add_pos', 'add_pts_to_date', 'add_pts_ROS',
        'drop_pos', 'drop_pts_to_date', 'drop_pts_ROS',
        'points_gained'
    ]]

    # Iterate through rows where manager is 'Unknown' and find the correct owner from player_df
    for index, row in aggregated_df[aggregated_df['manager'] == 'Unknown'].iterrows():
        player_name = row['dropped_player']
        year = row['year']
        previous_owner = player_df[(player_df['player'] == player_name) & (player_df['season'] == int(year))]['owner']
        if not previous_owner.empty:
            aggregated_df.at[index, 'manager'] = previous_owner.iloc[0]

    if include_search_bars and keys:
        # Add search bars in rows with unique keys
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

        # Filter the DataFrame based on search inputs
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

    # Display the merged data in a table without the index
    st.dataframe(aggregated_df, hide_index=True)