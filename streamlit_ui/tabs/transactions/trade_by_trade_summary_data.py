import pandas as pd
import streamlit as st

def display_trade_by_trade_summary_data(transaction_df, player_df, draft_history_df):
    # Ensure nickname column has no missing values before merge
    transaction_df['nickname'].fillna('Unknown', inplace=True)

    # Remove duplicate rows in transaction_df based on transaction_id and name
    transaction_df.drop_duplicates(subset=['transaction_id', 'name'], inplace=True)

    # Filter only trade transactions
    trade_transactions = transaction_df[transaction_df['transaction_type'] == 'trade']

    # Remove duplicate rows in player_df based on player, week, and season
    player_df.drop_duplicates(subset=['player', 'week', 'season'], inplace=True)

    # Remove duplicate rows in draft_history_df based on Name Full and Year
    draft_history_df.drop_duplicates(subset=['Name Full', 'Year'], inplace=True)

    # Merge draft history data with trade transactions
    trade_transactions = pd.merge(trade_transactions, draft_history_df[['Name Full', 'Year', 'Cost', 'Is Keeper Status']],
                                  left_on=['name', 'year'], right_on=['Name Full', 'Year'], how='left')

    # Merge the dataframes for Weekly Trades using left join, selecting only necessary columns
    merged_df = pd.merge(trade_transactions[['transaction_id', 'name', 'week', 'year', 'transaction_type', 'faab_bid', 'nickname', 'Cost', 'Is Keeper Status']],
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

    # Calculate Rest of Season Position Rank
    merged_df['Rest_of_Season_Rank'] = merged_df.groupby('position')['points_week_17'].rank(ascending=False, method='min')
    merged_df['Rest_of_Season_Rank'] = merged_df['Rest_of_Season_Rank'].fillna(0).astype(int)
    merged_df['Rest_of_Season_Rank'] = merged_df['position'] + merged_df['Rest_of_Season_Rank'].astype(str)

    # Rename columns
    merged_df.rename(columns={
        'faab_bid': 'faab',
        'nickname': 'manager'
    }, inplace=True)

    # Add a boolean column for "Is Keeper Status"
    merged_df['Is Keeper'] = merged_df['Is Keeper Status']

    # Function to sort names and ranks
    def sort_names_ranks(names, ranks):
        combined = list(zip(names, ranks))
        combined.sort(key=lambda x: int(''.join(filter(str.isdigit, x[1])) if ''.join(filter(str.isdigit, x[1])) else '0'))
        sorted_names, sorted_ranks = zip(*combined)
        return ', '.join(sorted_names), ', '.join(sorted_ranks)

    # Aggregate data by transaction_id and manager, summing the Is Keeper column and joining names with a comma
    aggregated_df = merged_df.groupby(['transaction_id', 'manager']).agg({
        'week': 'first',
        'year': 'first',
        'name': lambda x: ', '.join(x),
        'points_transaction_week': 'sum',
        'points_week_17': 'sum',
        'Cost': 'sum',
        'Is Keeper': 'sum',
        'Rest_of_Season_Rank': lambda x: ', '.join(x.astype(str))
    }).reset_index()

    # Sort names and ranks
    aggregated_df[['name', 'Rest_of_Season_Rank']] = aggregated_df.apply(
        lambda row: sort_names_ranks(row['name'].split(', '), row['Rest_of_Season_Rank'].split(', ')),
        axis=1, result_type='expand'
    )

    # Create a DataFrame for traded away players
    traded_away_df = merged_df.copy()
    traded_away_df.rename(columns={
        'name': 'traded_away_name',
        'points_transaction_week': 'traded_away_points_transaction_week',
        'points_week_17': 'traded_away_points_week_17',
        'Cost': 'traded_away_Cost',
        'Is Keeper': 'traded_away_Is Keeper',
        'Rest_of_Season_Rank': 'traded_away_Rest_of_Season_Rank'
    }, inplace=True)

    # Aggregate traded away data by transaction_id and manager
    traded_away_aggregated_df = traded_away_df.groupby(['transaction_id', 'manager']).agg({
        'traded_away_name': lambda x: ', '.join(x),
        'traded_away_points_transaction_week': 'sum',
        'traded_away_points_week_17': 'sum',
        'traded_away_Cost': 'sum',
        'traded_away_Is Keeper': 'sum',
        'traded_away_Rest_of_Season_Rank': lambda x: ', '.join(x.astype(str))
    }).reset_index()

    # Sort traded away names and ranks
    traded_away_aggregated_df[['traded_away_name', 'traded_away_Rest_of_Season_Rank']] = traded_away_aggregated_df.apply(
        lambda row: sort_names_ranks(row['traded_away_name'].split(', '), row['traded_away_Rest_of_Season_Rank'].split(', ')),
        axis=1, result_type='expand'
    )

    # Merge the traded away aggregated DataFrame with the aggregated DataFrame based on transaction_id
    final_df = pd.merge(aggregated_df, traded_away_aggregated_df, on='transaction_id', suffixes=('', '_away'))
    final_df = final_df[final_df['manager'] != final_df['manager_away']]

    # Calculate points gained in trade
    final_df['points_gained_in_trade'] = final_df['points_week_17'] - final_df['traded_away_points_week_17']

    # Add trade partner column
    final_df['trade_partner'] = final_df['manager_away']

    # Ensure the year column is displayed without a comma
    final_df['year'] = final_df['year'].astype(int).astype(str)

    # Remove duplicate rows
    final_df.drop_duplicates(inplace=True)

    # Specify the column order directly
    final_df = final_df[[
        'manager', 'trade_partner', 'week', 'year', 'name', 'Rest_of_Season_Rank', 'traded_away_name', 'traded_away_Rest_of_Season_Rank', 'Is Keeper', 'points_gained_in_trade', 'points_transaction_week',
        'points_week_17',  'traded_away_points_transaction_week', 'traded_away_points_week_17', 'traded_away_Cost',
        'traded_away_Is Keeper','Cost', 'transaction_id',
    ]]

    # Rename columns for clarity
    final_df.rename(columns={
        'transaction_id': 'id',
        'manager': 'mngr',
        'trade_partner': 'prtnr',
        'week': 'wk',
        'year': 'yr',
        'name': 'acquired',
        'Rest_of_Season_Rank': 'acquired_rank',
        'traded_away_name': 'traded_away',
        'traded_away_Rest_of_Season_Rank': 'traded_away_rank',
        'points_gained_in_trade': 'pts_gained',
        'Is Keeper': 'nxt_yr_keeper',
        'points_transaction_week': 'acqrd_pre_trade_pts',
        'points_week_17': 'acqrd_pts_post_trade',
        'Cost': 'next_yr_draft_price',
        'traded_away_points_transaction_week': 'traded_away_pts_pre_trade',
        'traded_away_points_week_17': 'traded_away_pts_post_trade',
        'traded_away_Cost': 'traded_away_price_next_year',
        'traded_away_Is Keeper': 'traded_away_keeper',
    }, inplace=True)

    # Initialize trade_summary_df in session state
    st.session_state['trade_summary_df'] = final_df

    # Add search bars
    col1, col2, col3 = st.columns(3)
    with col1:
        year_search = st.selectbox('Search by Year', options=['All'] + list(final_df['yr'].unique()), key='year_search_trades_summary')
    with col2:
        name_search = st.text_input('Search by Player Name', key='player_search_trades_summary')
    with col3:
        nickname_search = st.text_input('Search by Manager', key='nickname_search_trades_summary')

    # Filter the DataFrame based on search inputs
    filtered_df = final_df.copy()
    if year_search and year_search != 'All':
        filtered_df = filtered_df[filtered_df['yr'] == year_search]
    if nickname_search:
        filtered_df = filtered_df[filtered_df['mngr'].str.contains(nickname_search, case=False, na=False)]
    if name_search:
        filtered_df = filtered_df[filtered_df['acquired'].str.contains(name_search, case=False, na=False)]

    # Display the final data in a table without the index
    st.dataframe(filtered_df, hide_index=True)