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

    # Ensure manager column has no missing values before merge
    transaction_df['manager'].fillna('Unknown', inplace=True)

    transaction_df.drop_duplicates(subset=['transaction_id', 'player_name'], inplace=True)
    trade_transactions = transaction_df[transaction_df['transaction_type'] == 'trade']
    player_df.drop_duplicates(subset=['player_name', 'week', 'year'], inplace=True)
    draft_history_df.drop_duplicates(subset=['player_name', 'year'], inplace=True)
    draft_history_df['year'] = draft_history_df['year'].astype(int)
    draft_history_df['year'] = draft_history_df['year'] - 1

    trade_transactions = pd.merge(
        trade_transactions,
        draft_history_df[['player_name', 'year', 'cost', 'is_keeper_status']],
        left_on=['player_name', 'year'],
        right_on=['player_name', 'year'],
        how='left'
    )

    merged_df = pd.merge(
        trade_transactions[['transaction_id', 'player_name', 'week', 'year', 'transaction_type', 'faab_bid', 'manager', 'cost', 'is_keeper_status']],
        player_df[['player_name', 'week', 'year', 'rolling_point_total', 'yahoo_position']],
        left_on=['player_name', 'week', 'year'],
        right_on=['player_name', 'week', 'year'],
        how='left'
    )

    merged_df['manager'].fillna('Unknown', inplace=True)

    points_transaction_week = player_df.set_index(['player_name', 'year', 'week'])['rolling_point_total']
    merged_df['points_transaction_week'] = merged_df.set_index(['player_name', 'year', 'week']).index.map(points_transaction_week).fillna(0).values

    merged_df['Rank_on_Transaction_Date'] = merged_df.groupby('yahoo_position')['points_transaction_week'].rank(ascending=False, method='min')
    merged_df['Rank_on_Transaction_Date'] = merged_df['Rank_on_Transaction_Date'].fillna(0).astype(int)
    merged_df['Rank_on_Transaction_Date'] = merged_df['yahoo_position'] + merged_df['Rank_on_Transaction_Date'].astype(str)

    max_week_up_to_16 = player_df[(player_df['week'] <= 16) & (player_df['year'] <= 2020)].groupby(['player_name', 'year'])['week'].idxmax()
    max_week_up_to_17 = player_df[(player_df['week'] <= 17) & (player_df['year'] >= 2021)].groupby(['player_name', 'year'])['week'].idxmax()
    points_max_week_up_to_16 = player_df.loc[max_week_up_to_16].set_index(['player_name', 'year'])['rolling_point_total']
    points_max_week_up_to_17 = player_df.loc[max_week_up_to_17].set_index(['player_name', 'year'])['rolling_point_total']

    merged_df['points_week_max'] = merged_df.apply(
        lambda row: points_max_week_up_to_16.get((row['player_name'], row['year']), 0) if row['year'] <= 2020 else points_max_week_up_to_17.get((row['player_name'], row['year']), 0),
        axis=1
    )

    merged_df['points_week_max'] -= merged_df['points_transaction_week']

    merged_df['Rest_of_year_Rank'] = merged_df.groupby('yahoo_position')['points_week_max'].rank(ascending=False, method='min')
    merged_df['Rest_of_year_Rank'] = merged_df['Rest_of_year_Rank'].fillna(0).astype(int)
    merged_df['Rest_of_year_Rank'] = merged_df['yahoo_position'] + merged_df['Rest_of_year_Rank'].astype(str)

    merged_df['Rank_on_Transaction_Date_Int'] = merged_df['Rank_on_Transaction_Date'].str.extract(r'(\d+)').fillna(
        0).astype(int)
    merged_df['Rest_of_year_Rank_Int'] = merged_df['Rest_of_year_Rank'].str.extract(r'(\d+)').fillna(0).astype(int)
    merged_df['Change_in_Rank'] = merged_df['Rank_on_Transaction_Date_Int'] - merged_df['Rest_of_year_Rank_Int']

    merged_df.rename(columns={
        'faab_bid': 'faab'
    }, inplace=True)

    merged_df['Is Keeper'] = merged_df['is_keeper_status']
    merged_df['Is Keeper'] = merged_df['Is Keeper'].apply(lambda x: '✔️' if x == 1 else '')

    merged_df.drop(columns=['faab', 'players_same_manager', 'players_diff_manager', 'year_draft', 'is_keeper_status', 'Rank_on_Transaction_Date_Int', 'Rest_of_year_Rank_Int'], inplace=True, errors='ignore')
    merged_df['year'] = merged_df['year'].astype(int).astype(str)
    merged_df.drop_duplicates(inplace=True)

    merged_df = merged_df[[
        'transaction_id', 'manager', 'week', 'year', 'player_name', 'yahoo_position', 'points_transaction_week', 'Rank_on_Transaction_Date', 'points_week_max', 'Rest_of_year_Rank', 'Change_in_Rank', 'cost', 'Is Keeper'
    ]]

    col1, col2, col3 = st.columns(3)
    with col1:
        year_search = st.selectbox('Search by year', options=['All'] + list(merged_df['year'].unique()), key='year_search_trades')
    with col2:
        name_search = st.text_input('Search by Player Name', key='player_search_trades')
    with col3:
        manager_search = st.text_input('Search by Manager', key='manager_search_trades')

    if year_search and year_search != 'All':
        merged_df = merged_df[merged_df['year'] == year_search]
    if manager_search:
        merged_df = merged_df[merged_df['manager'].str.contains(manager_search, case=False, na=False)]
    if name_search:
        merged_df = merged_df[merged_df['player_name'].str.contains(name_search, case=False, na=False)]

    st.dataframe(merged_df, hide_index=True)