import pandas as pd
import streamlit as st
from . import trade_overview
from . import add_drop_overview
from . import combo_transaction_overview

class AllTransactionsViewer:
    def __init__(self, transaction_df, player_df, injury_df, draft_history_df):
        self.transaction_df = transaction_df
        self.player_df = player_df
        self.injury_df = injury_df
        self.draft_history_df = draft_history_df

    def display(self):
        # Create main tabs
        tab_names = ["Add/Drop", "Trades", "Total Transactions"]
        tabs = st.tabs(tab_names)

        with tabs[0]:
            add_drop_overview.display_add_drop(self.transaction_df, self.player_df, self.injury_df)

        with tabs[1]:
            trade_overview.display_trades(self.transaction_df, self.player_df, self.injury_df, self.draft_history_df)

        with tabs[2]:
            combo_transaction_overview.AllTransactionOverview(self.transaction_df, self.player_df, self.injury_df, self.draft_history_df).display()