import pandas as pd
import streamlit as st

def display_career_trade_data(transaction_df, player_df, draft_history_df):
    # Read the displayed data from Streamlit's session state
    trade_summary_df = st.session_state['trade_summary_df']

    # Aggregate data by manager
    career_aggregated_df = trade_summary_df.groupby(['mngr']).agg({
        'id': 'count',
        'nxt_yr_keeper': 'sum',
        'acqrd_pre_trade_pts': 'sum',
        'acqrd_pts_post_trade': 'sum',
        'traded_away_pts_pre_trade': 'sum',
        'traded_away_pts_post_trade': 'sum',
        'pts_gained': 'sum'
    }).reset_index()

    # Rename columns for clarity
    career_aggregated_df.rename(columns={
        'mngr': 'manager',
        'id': 'trades_made',
        'nxt_yr_keeper': 'keepers_added',
        'acqrd_pre_trade_pts': 'acquired_pts_pre_trade',
        'acqrd_pts_post_trade': 'acquired_pts_post_trade',
        'traded_away_pts_pre_trade': 'traded_pts_pre_trade',
        'traded_away_pts_post_trade': 'traded_pts_post_trade',
        'pts_gained': 'pts_gained_in_trade'
    }, inplace=True)

    # Display the aggregated data in a table without the index
    st.dataframe(career_aggregated_df, hide_index=True, key='career_aggregated_df_' + str(id(career_aggregated_df)))