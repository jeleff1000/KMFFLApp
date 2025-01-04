import pandas as pd
import streamlit as st

def display_trades(transaction_df, player_df, injury_df):
    # Create specific tabs for Trades
    sub_tab_names = ["Weekly", "Season", "Career"]
    sub_tabs = st.tabs(sub_tab_names)

    for i, sub_tab_name in enumerate(sub_tab_names):
        with sub_tabs[i]:
            st.subheader(sub_tab_name)
            # Placeholder for Trades data
            st.write(f"{sub_tab_name} Trades data will be displayed here.")