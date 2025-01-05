import pandas as pd
import streamlit as st
from .traded_player_data import display_traded_player_data
from .trade_by_trade_summary_data import display_trade_by_trade_summary_data
from .season_trade_data import display_season_trade_data
from .career_trade_data import display_career_trade_data

def display_trades(transaction_df, player_df, injury_df, draft_history_df):
    # Create specific tabs for Trades
    sub_tab_names = ["Traded Player Data", "Trade Summaries", "Season", "Career"]
    sub_tabs = st.tabs(sub_tab_names)

    for i, sub_tab_name in enumerate(sub_tab_names):
        with sub_tabs[i]:
            st.subheader(sub_tab_name)
            if sub_tab_name == "Traded Player Data":
                display_traded_player_data(transaction_df, player_df, draft_history_df)
            elif sub_tab_name == "Trade Summaries":
                display_trade_by_trade_summary_data(transaction_df, player_df, draft_history_df)
            elif sub_tab_name == "Season":
                display_season_trade_data(transaction_df, player_df, draft_history_df)
            elif sub_tab_name == "Career":
                display_career_trade_data(transaction_df, player_df, draft_history_df)