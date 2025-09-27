import pandas as pd
import streamlit as st

def display_traded_player_data(transaction_df, player_df, draft_history_df):
    # Remove duplicate player_name columns if present
    if 'player_name' in player_df.columns and 'player' in player_df.columns:
        player_df = player_df.drop(columns=['player_name'])
    if 'player' in player_df.columns:
        player_df = player_df.rename(columns={'player': 'player_name'})
    if 'player' in draft_history_df.columns and 'player_name' in draft_history_df.columns:
        draft_history_df = draft_history_df.drop(columns=['player_name'])
    if 'player' in draft_history_df.columns:
        draft_history_df = draft_history_df.rename(columns={'player': 'player_name'})


    # Ensure nickname column has no missing values before merge
    transaction_df['nickname'].fillna('Unknown', inplace=True)

    # Remove duplicate rows in transaction_df based on transaction_id and player_name
    transaction_df.drop_duplicates(subset=['transaction_id', 'player_name'], inplace=True)

    # Filter only trade transactions
    trade_transactions = transaction_df[transaction_df['transaction_type'] == 'trade']

    # Remove duplicate rows in player_df based on player_name, week, and year
    player_df.drop_duplicates(subset=['player_name', 'week', 'year'], inplace=True)

    # Remove duplicate rows in draft_history_df based on player_name and year
    draft_history_df.drop_duplicates(subset=['player_name', 'year'], inplace=True)

    # Ensure the 'year' column is of integer type
    draft_history_df['year'] = draft_history_df['year'].astype(int)

    # Adjust the year column in draft_history_df to be year - 1
    draft_history_df['year'] = draft_history_df['year'] - 1

    # Merge draft history data with trade transactions
    trade_transactions = pd.merge(
        trade_transactions,
        draft_history_df[['player_name', 'year', 'cost', 'is_keeper_status']],
        left_on=['player_name', 'year'],
        right_on=['player_name', 'year'],
        how='left'
    )

    # Merge the dataframes for Weekly Trades using left join, selecting only necessary columns
    merged_df = pd.merge(
        trade_transactions[['transaction_id', 'player_name', 'week', 'year', 'transaction_type', 'faab_bid', 'nickname', 'cost', 'is_keeper_status']],
        player_df[['player_name', 'week', 'year', 'rolling_point_total', 'position']],
        left_on=['player_name', 'week', 'year'],
        right_on=['player_name', 'week', 'year'],
        how='left'
    )

    # Ensure nickname column has no missing values after merge
    merged_df['nickname'].fillna('Unknown', inplace=True)

    # Calculate points for the transaction week
    points_transaction_week = player_df.set_index(['player_name', 'year', 'week'])['rolling_point_total']
    merged_df['points_transaction_week'] = merged_df.set_index(['player_name', 'year', 'week']).index.map(points_transaction_week).fillna(0).values

    # Calculate rank on transaction date
    merged_df['Rank_on_Transaction_Date'] = merged_df.groupby('position')['points_transaction_week'].rank(ascending=False, method='min')
    merged_df['Rank_on_Transaction_Date'] = merged_df['Rank_on_Transaction_Date'].fillna(0).astype(int)
    merged_df['Rank_on_Transaction_Date'] = merged_df['position'] + merged_df['Rank_on_Transaction_Date'].astype(str)

    # Find the maximum week up to week 16 for years 2020 and earlier, and up to week 17 for years 2021 and later
    max_week_up_to_16 = player_df[(player_df['week'] <= 16) & (player_df['year'] <= 2020)].groupby(['player_name', 'year'])['week'].idxmax()
    max_week_up_to_17 = player_df[(player_df['week'] <= 17) & (player_df['year'] >= 2021)].groupby(['player_name', 'year'])['week'].idxmax()
    points_max_week_up_to_16 = player_df.loc[max_week_up_to_16].set_index(['player_name', 'year'])['rolling_point_total']
    points_max_week_up_to_17 = player_df.loc[max_week_up_to_17].set_index(['player_name', 'year'])['rolling_point_total']

    # Map the points for the maximum week up to week 16 or 17 based on the year
    merged_df['points_week_max'] = merged_df.apply(
        lambda row: points_max_week_up_to_16.get((row['player_name'], row['year']), 0) if row['year'] <= 2020 else points_max_week_up_to_17.get((row['player_name'], row['year']), 0),
        axis=1
    )

    # Calculate the difference between the maximum week and the transaction week
    merged_df['points_week_max'] -= merged_df['points_transaction_week']

    # Calculate Rest of year Position Rank
    merged_df['Rest_of_year_Rank'] = merged_df.groupby('position')['points_week_max'].rank(ascending=False, method='min')
    merged_df['Rest_of_year_Rank'] = merged_df['Rest_of_year_Rank'].fillna(0).astype(int)
    merged_df['Rest_of_year_Rank'] = merged_df['position'] + merged_df['Rest_of_year_Rank'].astype(str)

    # Calculate change in rank
    merged_df['Rank_on_Transaction_Date_Int'] = merged_df['Rank_on_Transaction_Date'].str.extract('(\d+)').fillna(0).astype(int)
    merged_df['Rest_of_year_Rank_Int'] = merged_df['Rest_of_year_Rank'].str.extract('(\d+)').fillna(0).astype(int)
    merged_df['Change_in_Rank'] = merged_df['Rank_on_Transaction_Date_Int'] - merged_df['Rest_of_year_Rank_Int']

    # Rename columns
    merged_df.rename(columns={
        'faab_bid': 'faab',
        'nickname': 'manager'
    }, inplace=True)

    # Add a boolean column for "is_keeper_status"
    merged_df['Is Keeper'] = merged_df['is_keeper_status']

    # Convert "Is Keeper" to gray check mark
    merged_df['Is Keeper'] = merged_df['Is Keeper'].apply(lambda x: '✔️' if x == 1 else '')

    # Remove the specified columns
    merged_df.drop(columns=['faab', 'players_same_manager', 'players_diff_manager', 'year_draft', 'is_keeper_status', 'Rank_on_Transaction_Date_Int', 'Rest_of_year_Rank_Int'], inplace=True, errors='ignore')

    # Ensure the year column is displayed without a comma
    merged_df['year'] = merged_df['year'].astype(int).astype(str)

    # Remove duplicate rows
    merged_df.drop_duplicates(inplace=True)

    # Specify the column order directly
    merged_df = merged_df[[
        'transaction_id', 'manager', 'week', 'year', 'player_name', 'position', 'points_transaction_week', 'Rank_on_Transaction_Date', 'points_week_max', 'Rest_of_year_Rank', 'Change_in_Rank', 'cost', 'Is Keeper'
    ]]

    # Add search bars in rows
    col1, col2, col3 = st.columns(3)
    with col1:
        year_search = st.selectbox('Search by year', options=['All'] + list(merged_df['year'].unique()), key='year_search_trades')
    with col2:
        name_search = st.text_input('Search by Player Name', key='player_search_trades')
    with col3:
        nickname_search = st.text_input('Search by Manager', key='nickname_search_trades')

    # Filter the DataFrame based on search inputs
    if year_search and year_search != 'All':
        merged_df = merged_df[merged_df['year'] == year_search]
    if nickname_search:
        merged_df = merged_df[merged_df['manager'].str.contains(nickname_search, case=False, na=False)]
    if name_search:
        merged_df = merged_df[merged_df['player_name'].str.contains(name_search, case=False, na=False)]

    # Display the merged data in a table without the index
    st.dataframe(merged_df, hide_index=True)