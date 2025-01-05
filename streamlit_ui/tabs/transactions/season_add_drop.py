import pandas as pd
import streamlit as st

def display_season_add_drop(transaction_df, player_df, return_df=False):
    # Ensure nickname column has no missing values before merge
    transaction_df['nickname'].fillna('Unknown', inplace=True)

    # Merge the dataframes for Weekly Add/Drop using left join, selecting only necessary columns
    merged_df = pd.merge(transaction_df[['transaction_id', 'name', 'week', 'year', 'transaction_type', 'faab_bid', 'nickname']],
                         player_df[['player', 'week', 'season', 'rolling_point_total', 'position']],
                         left_on=['name', 'week', 'year'], right_on=['player', 'week', 'season'], how='left')

    # Ensure nickname column has no missing values after merge
    merged_df['nickname'].fillna('Unknown', inplace=True)

    # Create new columns based on transaction type
    merged_df['add_points_transaction_week'] = merged_df['rolling_point_total'].where(merged_df['transaction_type'] == 'add', 0)
    merged_df['add_points_week_17'] = merged_df['rolling_point_total'].where(merged_df['transaction_type'] == 'add', 0)
    merged_df['drop_points_transaction_week'] = merged_df['rolling_point_total'].where(merged_df['transaction_type'] == 'drop', 0)
    merged_df['drop_points_week_17'] = merged_df['rolling_point_total'].where(merged_df['transaction_type'] == 'drop', 0)

    # Only calculate faab for adds
    merged_df['faab_add'] = merged_df['faab_bid'].where(merged_df['transaction_type'] == 'add', 0)

    # Filter only add transactions for counting
    add_transactions = merged_df[merged_df['transaction_type'] == 'add']

    # Group by year and manager and aggregate the necessary columns
    aggregated_df = merged_df.groupby(['year', 'nickname']).agg({
        'faab_add': 'sum',
        'add_points_transaction_week': 'sum',
        'add_points_week_17': 'sum',
        'drop_points_transaction_week': 'sum',
        'drop_points_week_17': 'sum'
    }).reset_index()

    # Add the count of add transactions
    add_transaction_count = add_transactions.groupby(['year', 'nickname']).size().reset_index(name='transaction_count')
    aggregated_df = pd.merge(aggregated_df, add_transaction_count, on=['year', 'nickname'], how='left')

    # Calculate points gained
    aggregated_df['points_gained'] = aggregated_df['add_points_week_17'] - aggregated_df['drop_points_week_17']

    # Convert year to integer and then to string without formatting
    aggregated_df['year'] = aggregated_df['year'].astype(int).astype(str)

    # Rename columns
    aggregated_df.rename(columns={
        'faab_add': 'faab',
        'add_points_transaction_week': 'add_pts_to_date',
        'drop_points_transaction_week': 'drop_pts_to_date',
        'add_points_week_17': 'add_pts_ROS',
        'drop_points_week_17': 'drop_pts_ROS',
        'nickname': 'manager'
    }, inplace=True)

    # Specify the column order directly
    aggregated_df = aggregated_df[[
        'manager', 'year', 'faab', 'add_pts_to_date', 'add_pts_ROS', 'drop_pts_to_date', 'drop_pts_ROS', 'points_gained', 'transaction_count'
    ]]

    if return_df:
        return aggregated_df

    # Add search bars in rows
    col1, col2 = st.columns(2)
    with col1:
        year_search = st.selectbox('Search by Year', options=['All'] + list(aggregated_df['year'].unique()), key='year_search_season')
    with col2:
        nickname_search = st.text_input('Search by Manager', key='nickname_search_season')

    # Filter the DataFrame based on search inputs
    if year_search and year_search != 'All':
        aggregated_df = aggregated_df[aggregated_df['year'] == year_search]
    if nickname_search:
        aggregated_df = aggregated_df[aggregated_df['manager'].str.contains(nickname_search, case=False, na=False)]

    # Display the merged data in a table without the index
    st.dataframe(aggregated_df, hide_index=True)