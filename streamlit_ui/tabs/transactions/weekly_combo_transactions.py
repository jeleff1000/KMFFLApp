import pandas as pd
import streamlit as st

def display_weekly_combo_transactions(transaction_df, player_df, draft_history_df):
    def merge_and_calculate_points(transaction_df, player_df, columns):
        merged_df = pd.merge(
            transaction_df[columns['transaction']],
            player_df[columns['player']],
            left_on=['player_name', 'week', 'year'],
            right_on=['player', 'week', 'year'],
            how='left'
        )
        merged_df['manager'].fillna('Unknown', inplace=True)
        points_transaction_week = player_df.set_index(['player', 'year', 'week'])['rolling_point_total']
        merged_df['points_transaction_week'] = (
            merged_df.set_index(['player_name', 'year', 'week']).index
            .map(points_transaction_week).fillna(0).values
        )

        max_week_up_to_16 = (
            player_df[(player_df['week'] <= 16) & (player_df['year'] <= 2020)]
            .groupby(['player', 'year'])['week'].idxmax()
        )
        max_week_up_to_17 = (
            player_df[(player_df['week'] <= 17) & (player_df['year'] >= 2021)]
            .groupby(['player', 'year'])['week'].idxmax()
        )
        points_max_week_up_to_16 = player_df.loc[max_week_up_to_16].set_index(['player', 'year'])['rolling_point_total']
        points_max_week_up_to_17 = player_df.loc[max_week_up_to_17].set_index(['player', 'year'])['rolling_point_total']

        merged_df['points_week_max'] = merged_df.apply(
            lambda row: points_max_week_up_to_16.get((row['player_name'], row['year']), 0)
            if row['year'] <= 2020 else
            points_max_week_up_to_17.get((row['player_name'], row['year']), 0),
            axis=1
        )

        merged_df['points_week_max'] -= merged_df['points_transaction_week']
        return merged_df

    def get_weekly_add_drop_data(transaction_df, player_df):
        # ensure 'manager' exists (fallback from 'nickname' or fill Unknown)
        if 'manager' not in transaction_df.columns:
            if 'nickname' in transaction_df.columns:
                transaction_df = transaction_df.rename(columns={'nickname': 'manager'})
            else:
                transaction_df['manager'] = 'Unknown'

        columns = {
            'transaction': ['transaction_id', 'player_name', 'week', 'year', 'transaction_type', 'faab_bid', 'manager'],
            'player': ['player', 'week', 'year', 'rolling_point_total', 'position']
        }
        merged_df = merge_and_calculate_points(transaction_df, player_df, columns)

        merged_df['added_player']   = merged_df['player_name'].where(merged_df['transaction_type'] == 'add')
        merged_df['dropped_player'] = merged_df['player_name'].where(merged_df['transaction_type'] == 'drop')

        merged_df['add_points_transaction_week']  = merged_df['points_transaction_week'].where(merged_df['transaction_type'] == 'add')
        merged_df['add_points_week_max']          = merged_df['points_week_max'].where(merged_df['transaction_type'] == 'add')
        merged_df['drop_points_transaction_week'] = merged_df['points_transaction_week'].where(merged_df['transaction_type'] == 'drop')
        merged_df['drop_points_week_max']         = merged_df['points_week_max'].where(merged_df['transaction_type'] == 'drop')

        aggregated_df = merged_df.groupby('transaction_id').agg({
            'manager': 'first',
            'week': 'first',
            'year': 'first',
            'added_player': 'first',
            'dropped_player': 'first',
            'add_points_transaction_week': 'first',
            'add_points_week_max': 'first',
            'drop_points_transaction_week': 'first',
            'drop_points_week_max': 'first'
        }).reset_index()

        aggregated_df['points_gained'] = aggregated_df['add_points_week_max'] - aggregated_df['drop_points_week_max']
        aggregated_df['year'] = aggregated_df['year'].astype(int).astype(str)

        aggregated_df.rename(columns={
            'add_points_transaction_week':  'add_pts_to_date',
            'drop_points_transaction_week': 'drop_pts_to_date',
            'add_points_week_max':          'add_pts_ros',
            'drop_points_week_max':         'drop_pts_ROS'
        }, inplace=True)

        return aggregated_df[[
            'manager', 'week', 'year',
            'added_player', 'dropped_player',
            'add_pts_to_date', 'add_pts_ros',
            'drop_pts_to_date', 'drop_pts_ROS',
            'points_gained'
        ]]

    def get_trade_summary_data(transaction_df, player_df, draft_history_df):
        # ---- NEW: mirror the same guard here ----
        if 'manager' not in transaction_df.columns:
            if 'nickname' in transaction_df.columns:
                transaction_df = transaction_df.rename(columns={'nickname': 'manager'})
            else:
                transaction_df['manager'] = 'Unknown'
        # -----------------------------------------

        transaction_df['manager'].fillna('Unknown', inplace=True)
        transaction_df.drop_duplicates(subset=['transaction_id', 'player_name'], inplace=True)
        trade_transactions = transaction_df[transaction_df['transaction_type'] == 'trade']
        player_df.drop_duplicates(subset=['player', 'week', 'year'], inplace=True)
        draft_history_df.drop_duplicates(subset=['player_name', 'year'], inplace=True)

        trade_transactions = pd.merge(
            trade_transactions,
            draft_history_df[['player_name', 'year', 'cost', 'is_keeper_status']],
            on=['player_name', 'year'],
            how='left'
        )

        columns = {
            'transaction': ['transaction_id', 'player_name', 'week', 'year', 'transaction_type', 'faab_bid', 'manager', 'cost', 'is_keeper_status'],
            'player': ['player', 'week', 'year', 'rolling_point_total', 'position']
        }
        merged_df = merge_and_calculate_points(trade_transactions, player_df, columns)

        merged_df['Rest_of_year_Rank'] = (
            merged_df.groupby('position')['points_week_max']
                     .rank(ascending=False, method='min')
                     .fillna(0).astype(int)
        )
        merged_df['Rest_of_year_Rank'] = merged_df['position'] + merged_df['Rest_of_year_Rank'].astype(str)
        merged_df['Is Keeper'] = merged_df['is_keeper_status']

        def sort_names_ranks(names, ranks):
            combined = list(zip(names, ranks))
            combined.sort(key=lambda x: int(''.join(filter(str.isdigit, x[1])) or '0'))
            sorted_names, sorted_ranks = zip(*combined)
            return ', '.join(sorted_names), ', '.join(sorted_ranks)

        aggregated_df = merged_df.groupby(['transaction_id', 'manager']).agg({
            'week': 'first',
            'year': 'first',
            'player_name': lambda x: ', '.join(x),
            'points_transaction_week': 'sum',
            'points_week_max': 'sum',
            'cost': 'sum',
            'Is Keeper': 'sum',
            'Rest_of_year_Rank': lambda x: ', '.join(x.astype(str))
        }).reset_index()

        aggregated_df[['player_name', 'Rest_of_year_Rank']] = aggregated_df.apply(
            lambda row: sort_names_ranks(row['player_name'].split(', '), row['Rest_of_year_Rank'].split(', ')),
            axis=1, result_type='expand'
        )

        traded_away_df = merged_df.copy()
        traded_away_df.rename(columns={
            'player_name': 'traded_away_name',
            'points_transaction_week': 'traded_away_points_transaction_week',
            'points_week_max': 'traded_away_points_week_max',
            'cost': 'traded_away_cost',
            'Is Keeper': 'traded_away_Is Keeper',
            'Rest_of_year_Rank': 'traded_away_Rest_of_year_Rank'
        }, inplace=True)

        traded_away_aggregated_df = traded_away_df.groupby(['transaction_id', 'manager']).agg({
            'traded_away_name': lambda x: ', '.join(x),
            'traded_away_points_transaction_week': 'sum',
            'traded_away_points_week_max': 'sum',
            'traded_away_cost': 'sum',
            'traded_away_Is Keeper': 'sum',
            'traded_away_Rest_of_year_Rank': lambda x: ', '.join(x.astype(str))
        }).reset_index()

        traded_away_aggregated_df[['traded_away_name', 'traded_away_Rest_of_year_Rank']] = traded_away_aggregated_df.apply(
            lambda row: sort_names_ranks(row['traded_away_name'].split(', '), row['traded_away_Rest_of_year_Rank'].split(', ')),
            axis=1, result_type='expand'
        )

        final_df = pd.merge(aggregated_df, traded_away_aggregated_df, on='transaction_id', suffixes=('', '_away'))
        final_df = final_df[final_df['manager'] != final_df['manager_away']]
        final_df['points_gained'] = final_df['points_week_max'] - final_df['traded_away_points_week_max']
        final_df['trade_partner'] = final_df['manager_away']
        final_df['year'] = final_df['year'].astype(int).astype(str)
        final_df.drop_duplicates(inplace=True)

        # No renaming: build expected output columns directly
        final_df['added_player']      = final_df['player_name']
        final_df['dropped_player']    = final_df['traded_away_name']
        final_df['add_pts_to_date']   = final_df['points_transaction_week']
        final_df['add_pts_ros']       = final_df['points_week_max']
        final_df['drop_pts_to_date']  = final_df['traded_away_points_transaction_week']
        final_df['drop_pts_ROS']      = final_df['traded_away_points_week_max']

        return final_df[[
            'manager', 'week', 'year',
            'added_player', 'dropped_player',
            'add_pts_to_date', 'add_pts_ros',
            'drop_pts_to_date', 'drop_pts_ROS',
            'points_gained'
        ]]

    weekly_add_drop_df = get_weekly_add_drop_data(transaction_df, player_df)
    trade_summary_df  = get_trade_summary_data(transaction_df, player_df, draft_history_df)
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
