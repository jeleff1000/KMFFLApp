import pandas as pd
import streamlit as st

def display_traded_player_data(transaction_df, player_df, draft_history_df):
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

    # Adjust the Year column in draft_history_df to be year - 1
    draft_history_df['Year'] = draft_history_df['Year'] - 1

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

    # Rename columns
    merged_df.rename(columns={
        'faab_bid': 'faab',
        'nickname': 'manager'
    }, inplace=True)

    # Add a boolean column for "Is Keeper Status"
    merged_df['Is Keeper'] = merged_df['Is Keeper Status']

    # Convert "Is Keeper" to gray check mark
    merged_df['Is Keeper'] = merged_df['Is Keeper'].apply(lambda x: '✔️' if x == 1 else '')

    # Remove the specified columns
    merged_df.drop(columns=['faab', 'players_same_manager', 'players_diff_manager', 'Name Full', 'Year_draft', 'Is Keeper Status'], inplace=True, errors='ignore')

    # Ensure the year column is displayed without a comma
    merged_df['year'] = merged_df['year'].astype(int).astype(str)

    # Remove duplicate rows
    merged_df.drop_duplicates(inplace=True)

    # Specify the column order directly
    merged_df = merged_df[[
        'transaction_id', 'manager', 'week', 'year', 'name', 'position', 'points_transaction_week', 'points_week_17', 'Cost', 'Is Keeper'
    ]]

    # Add search bars in rows
    col1, col2, col3 = st.columns(3)
    with col1:
        year_search = st.selectbox('Search by Year', options=['All'] + list(merged_df['year'].unique()), key='year_search_trades')
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
        merged_df = merged_df[merged_df['name'].str.contains(name_search, case=False, na=False)]

    # Display the merged data in a table without the index
    st.dataframe(merged_df, hide_index=True)