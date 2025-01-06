import pandas as pd
import streamlit as st

def display_weekly_combo_transactions(transaction_df, player_df, draft_history_df):
    def merge_and_calculate_points(transaction_df, player_df, columns):
        merged_df = pd.merge(transaction_df[columns['transaction']],
                             player_df[columns['player']],
                             left_on=['name', 'week', 'year'], right_on=['player', 'week', 'season'], how='left')
        merged_df['nickname'].fillna('Unknown', inplace=True)
        points_transaction_week = player_df.set_index(['player', 'season', 'week'])['rolling_point_total']
        merged_df['points_transaction_week'] = merged_df.set_index(['name', 'year', 'week']).index.map(points_transaction_week).fillna(0).values
        max_week_up_to_17 = player_df[player_df['week'] <= 17].groupby(['player', 'season'])['week'].idxmax()
        points_max_week_up_to_17 = player_df.loc[max_week_up_to_17].set_index(['player', 'season'])['rolling_point_total']
        merged_df['points_week_17'] = merged_df.set_index(['name', 'year']).index.map(points_max_week_up_to_17).fillna(0).values
        merged_df['points_week_17'] -= merged_df['points_transaction_week']
        return merged_df

    def get_weekly_add_drop_data(transaction_df, player_df):
        columns = {
            'transaction': ['transaction_id', 'name', 'week', 'year', 'transaction_type', 'faab_bid', 'nickname'],
            'player': ['player', 'week', 'season', 'rolling_point_total', 'position']
        }
        merged_df = merge_and_calculate_points(transaction_df, player_df, columns)
        merged_df['added_player'] = merged_df['name'].where(merged_df['transaction_type'] == 'add')
        merged_df['dropped_player'] = merged_df['name'].where(merged_df['transaction_type'] == 'drop')
        merged_df['add_points_transaction_week'] = merged_df['points_transaction_week'].where(merged_df['transaction_type'] == 'add')
        merged_df['add_points_week_17'] = merged_df['points_week_17'].where(merged_df['transaction_type'] == 'add')
        merged_df['drop_points_transaction_week'] = merged_df['points_transaction_week'].where(merged_df['transaction_type'] == 'drop')
        merged_df['drop_points_week_17'] = merged_df['points_week_17'].where(merged_df['transaction_type'] == 'drop')
        aggregated_df = merged_df.groupby('transaction_id').agg({
            'nickname': 'first', 'week': 'first', 'year': 'first', 'added_player': 'first', 'dropped_player': 'first',
            'add_points_transaction_week': 'first', 'add_points_week_17': 'first', 'drop_points_transaction_week': 'first',
            'drop_points_week_17': 'first'
        }).reset_index()
        aggregated_df['points_gained'] = aggregated_df['add_points_week_17'] - aggregated_df['drop_points_week_17']
        aggregated_df['year'] = aggregated_df['year'].astype(int).astype(str)
        aggregated_df.rename(columns={
            'add_points_transaction_week': 'add_pts_to_date', 'drop_points_transaction_week': 'drop_pts_to_date',
            'add_points_week_17': 'add_pts_ros', 'drop_points_week_17': 'drop_pts_ROS', 'nickname': 'manager'
        }, inplace=True)
        return aggregated_df[[
            'manager', 'week', 'year', 'added_player', 'dropped_player', 'add_pts_to_date', 'add_pts_ros',
            'drop_pts_to_date', 'drop_pts_ROS', 'points_gained'
        ]]

    def get_trade_summary_data(transaction_df, player_df, draft_history_df):
        transaction_df['nickname'].fillna('Unknown', inplace=True)
        transaction_df.drop_duplicates(subset=['transaction_id', 'name'], inplace=True)
        trade_transactions = transaction_df[transaction_df['transaction_type'] == 'trade']
        player_df.drop_duplicates(subset=['player', 'week', 'season'], inplace=True)
        draft_history_df.drop_duplicates(subset=['Name Full', 'Year'], inplace=True)
        trade_transactions = pd.merge(trade_transactions, draft_history_df[['Name Full', 'Year', 'Cost', 'Is Keeper Status']],
                                      left_on=['name', 'year'], right_on=['Name Full', 'Year'], how='left')
        columns = {
            'transaction': ['transaction_id', 'name', 'week', 'year', 'transaction_type', 'faab_bid', 'nickname', 'Cost', 'Is Keeper Status'],
            'player': ['player', 'week', 'season', 'rolling_point_total', 'position']
        }
        merged_df = merge_and_calculate_points(trade_transactions, player_df, columns)
        merged_df['Rest_of_Season_Rank'] = merged_df.groupby('position')['points_week_17'].rank(ascending=False, method='min').fillna(0).astype(int)
        merged_df['Rest_of_Season_Rank'] = merged_df['position'] + merged_df['Rest_of_Season_Rank'].astype(str)
        merged_df.rename(columns={'faab_bid': 'faab', 'nickname': 'manager'}, inplace=True)
        merged_df['Is Keeper'] = merged_df['Is Keeper Status']
        def sort_names_ranks(names, ranks):
            combined = list(zip(names, ranks))
            combined.sort(key=lambda x: int(''.join(filter(str.isdigit, x[1])) if ''.join(filter(str.isdigit, x[1])) else '0'))
            sorted_names, sorted_ranks = zip(*combined)
            return ', '.join(sorted_names), ', '.join(sorted_ranks)
        aggregated_df = merged_df.groupby(['transaction_id', 'manager']).agg({
            'week': 'first', 'year': 'first', 'name': lambda x: ', '.join(x), 'points_transaction_week': 'sum',
            'points_week_17': 'sum', 'Cost': 'sum', 'Is Keeper': 'sum', 'Rest_of_Season_Rank': lambda x: ', '.join(x.astype(str))
        }).reset_index()
        aggregated_df[['name', 'Rest_of_Season_Rank']] = aggregated_df.apply(
            lambda row: sort_names_ranks(row['name'].split(', '), row['Rest_of_Season_Rank'].split(', ')),
            axis=1, result_type='expand'
        )
        traded_away_df = merged_df.copy()
        traded_away_df.rename(columns={
            'name': 'traded_away_name', 'points_transaction_week': 'traded_away_points_transaction_week',
            'points_week_17': 'traded_away_points_week_17', 'Cost': 'traded_away_Cost', 'Is Keeper': 'traded_away_Is Keeper',
            'Rest_of_Season_Rank': 'traded_away_Rest_of_Season_Rank'
        }, inplace=True)
        traded_away_aggregated_df = traded_away_df.groupby(['transaction_id', 'manager']).agg({
            'traded_away_name': lambda x: ', '.join(x), 'traded_away_points_transaction_week': 'sum',
            'traded_away_points_week_17': 'sum', 'traded_away_Cost': 'sum', 'traded_away_Is Keeper': 'sum',
            'traded_away_Rest_of_Season_Rank': lambda x: ', '.join(x.astype(str))
        }).reset_index()
        traded_away_aggregated_df[['traded_away_name', 'traded_away_Rest_of_Season_Rank']] = traded_away_aggregated_df.apply(
            lambda row: sort_names_ranks(row['traded_away_name'].split(', '), row['traded_away_Rest_of_Season_Rank'].split(', ')),
            axis=1, result_type='expand'
        )
        final_df = pd.merge(aggregated_df, traded_away_aggregated_df, on='transaction_id', suffixes=('', '_away'))
        final_df = final_df[final_df['manager'] != final_df['manager_away']]
        final_df['points_gained_in_trade'] = final_df['points_week_17'] - final_df['traded_away_points_week_17']
        final_df['trade_partner'] = final_df['manager_away']
        final_df['year'] = final_df['year'].astype(int).astype(str)
        final_df.drop_duplicates(inplace=True)
        final_df.rename(columns={
            'transaction_id': 'id', 'manager': 'manager', 'trade_partner': 'prtnr', 'week': 'week', 'year': 'year',
            'name': 'added_player', 'Rest_of_Season_Rank': 'acquired_rank', 'traded_away_name': 'dropped_player',
            'traded_away_Rest_of_Season_Rank': 'traded_away_rank', 'points_gained_in_trade': 'points_gained',
            'Is Keeper': 'nxt_yr_keeper', 'points_transaction_week': 'add_pts_to_date', 'points_week_17': 'add_pts_ros',
            'Cost': 'next_yr_draft_price', 'traded_away_points_transaction_week': 'drop_pts_to_date',
            'traded_away_points_week_17': 'drop_pts_ROS', 'traded_away_Cost': 'traded_away_price_next_year',
            'traded_away_Is Keeper': 'traded_away_keeper'
        }, inplace=True)
        return final_df[[
            'manager', 'week', 'year', 'added_player', 'dropped_player', 'add_pts_to_date', 'add_pts_ros',
            'drop_pts_to_date', 'drop_pts_ROS', 'points_gained'
        ]]

    weekly_add_drop_df = get_weekly_add_drop_data(transaction_df, player_df)
    trade_summary_df = get_trade_summary_data(transaction_df, player_df, draft_history_df)
    combined_df = pd.concat([weekly_add_drop_df, trade_summary_df])

    col1, col2 = st.columns(2)
    with col1:
        manager_search = st.text_input('Search by Manager', key='manager_search')
        year_search = st.selectbox('Search by Year', options=['All'] + list(combined_df['year'].unique()), key='year_search')
    with col2:
        added_player_search = st.text_input('Search by Added Player', key='added_player_search')
        dropped_player_search = st.text_input('Search by Dropped Player', key='dropped_player_search')

    filtered_df = combined_df.copy()
    if manager_search:
        filtered_df = filtered_df[filtered_df['manager'].str.contains(manager_search, case=False, na=False)]
    if year_search and year_search != 'All':
        filtered_df = filtered_df[filtered_df['year'] == year_search]
    if added_player_search:
        filtered_df = filtered_df[filtered_df['added_player'].str.contains(added_player_search, case=False, na=False)]
    if dropped_player_search:
        filtered_df = filtered_df[filtered_df['dropped_player'].str.contains(dropped_player_search, case=False, na=False)]

    st.dataframe(filtered_df, hide_index=True)