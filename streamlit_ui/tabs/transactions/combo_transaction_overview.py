import pandas as pd
import streamlit as st
from ..transactions.weekly_combo_transactions import display_weekly_combo_transactions
from ..transactions.season_combo_transactions import display_season_all_transactions

class AllTransactionOverview:
    def __init__(self, transaction_df, player_df, injury_df, draft_history_df):
        self.transaction_df = transaction_df
        self.player_df = player_df
        self.injury_df = injury_df
        self.draft_history_df = draft_history_df
        self.trade_summary_df = self.load_trade_summary_df()
        self.weekly_add_drop_df = self.load_weekly_add_drop_df()

    def load_trade_summary_df(self):
        # Load or process the trade summary dataframe
        # Replace with actual loading logic
        return pd.DataFrame()

    def load_weekly_add_drop_df(self):
        # Load or process the weekly add/drop dataframe
        # Replace with actual loading logic
        return pd.DataFrame()

    def display(self):
        # Create tabs for weekly, season, and career views
        tab1, tab2, tab3 = st.tabs(["Weekly", "Season", "Career"])

        with tab1:
            # Display weekly combo transactions
            display_weekly_combo_transactions(self.transaction_df, self.player_df, self.draft_history_df)

        with tab2:
            # Display season combo transactions
            display_season_all_transactions(self.transaction_df, self.player_df, self.draft_history_df)

        with tab3:
            # Placeholder for career view
            st.write("Career view is under construction.")