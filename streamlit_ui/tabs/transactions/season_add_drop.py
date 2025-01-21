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
    merged_df['drop_points_transaction_week'] = merged_df['rolling_point_total'].where(merged_df['transaction_type'] == 'drop', 0)

    # Only calculate faab for adds
    merged_df['faab_add'] = merged_df['faab_bid'].where(merged_df['transaction_type'] == 'add', 0)

    # Filter only add transactions for counting
    add_transactions = merged_df[merged_df['transaction_type'] == 'add']

    # Find the maximum week up to week 16 for years 2020 and earlier, and up to week 17 for years 2021 and later
    max_week_up_to_16 = player_df[(player_df['week'] <= 16) & (player_df['season'] <= 2020)].groupby(['player', 'season'])['week'].idxmax()
    max_week_up_to_17 = player_df[(player_df['week'] <= 17) & (player_df['season'] >= 2021)].groupby(['player', 'season'])['week'].idxmax()
    points_max_week_up_to_16 = player_df.loc[max_week_up_to_16].set_index(['player', 'season'])['rolling_point_total']
    points_max_week_up_to_17 = player_df.loc[max_week_up_to_17].set_index(['player', 'season'])['rolling_point_total']

    # Map the points for the maximum week up to week 16 or 17 based on the year
    merged_df['points_week_max'] = merged_df.apply(
        lambda row: points_max_week_up_to_16.get((row['name'], row['year']), 0) if row['year'] <= 2020 else points_max_week_up_to_17.get((row['name'], row['year']), 0),
        axis=1
    )

    # Calculate the difference between the maximum week and the transaction week
    merged_df['add_points_week_max'] = merged_df['points_week_max'].where(merged_df['transaction_type'] == 'add', 0)
    merged_df['drop_points_week_max'] = merged_df['points_week_max'].where(merged_df['transaction_type'] == 'drop', 0)

    # Group by year and manager and aggregate the necessary columns
    aggregated_df = merged_df.groupby(['year', 'nickname']).agg({
        'faab_add': 'sum',
        'add_points_transaction_week': 'sum',
        'add_points_week_max': 'sum',
        'drop_points_transaction_week': 'sum',
        'drop_points_week_max': 'sum'
    }).reset_index()

    # Add the count of add transactions
    add_transaction_count = add_transactions.groupby(['year', 'nickname']).size().reset_index(name='transaction_count')
    aggregated_df = pd.merge(aggregated_df, add_transaction_count, on=['year', 'nickname'], how='left')

    # Calculate points gained
    aggregated_df['points_gained'] = aggregated_df['add_points_week_max'] - aggregated_df['drop_points_week_max']

    # Convert year to integer and then to string without formatting
    aggregated_df['year'] = aggregated_df['year'].astype(int).astype(str)

    # Rename columns
    aggregated_df.rename(columns={
        'faab_add': 'faab',
        'add_points_transaction_week': 'add_pts_to_date',
        'drop_points_transaction_week': 'drop_pts_to_date',
        'add_points_week_max': 'add_pts_ROS',
        'drop_points_week_max': 'drop_pts_ROS',
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