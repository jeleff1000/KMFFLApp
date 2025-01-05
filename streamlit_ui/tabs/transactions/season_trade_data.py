import pandas as pd
import streamlit as st

def display_season_trade_data(transaction_df, player_df, draft_history_df):
    # Read the displayed data from Streamlit's session state
    trade_summary_df = st.session_state['trade_summary_df']

    # Aggregate data by manager and year
    season_aggregated_df = trade_summary_df.groupby(['manager', 'year']).agg({
        'transaction_id': 'count',
        'Is Keeper': 'sum',
        'points_transaction_week': 'sum',
        'points_week_17': 'sum',
        'traded_away_points_transaction_week': 'sum',
        'traded_away_points_week_17': 'sum',
        'points_gained_in_trade': 'sum'
    }).reset_index()

    # Rename columns for clarity
    season_aggregated_df.rename(columns={
        'transaction_id': 'count_of_trades_made',
        'Is Keeper': 'count_of_keepers',
        'points_transaction_week': 'total_points_transaction_week',
        'points_week_17': 'total_points_week_17',
        'traded_away_points_transaction_week': 'total_traded_away_points_transaction_week',
        'traded_away_points_week_17': 'total_traded_away_points_week_17',
        'points_gained_in_trade': 'total_points_gained_in_trade'
    }, inplace=True)

    # Display the aggregated data in a table without the index
    st.dataframe(season_aggregated_df, hide_index=True, key='season_aggregated_df_' + str(id(season_aggregated_df)))