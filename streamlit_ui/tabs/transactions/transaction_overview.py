import pandas as pd
import streamlit as st
from . import trade_overview
from . import add_drop_overview

class AllTransactionsViewer:
    def __init__(self, transaction_df, player_df, injury_df, draft_history_df):
        self.transaction_df = transaction_df
        self.player_df = player_df
        self.injury_df = injury_df
        self.draft_history_df = draft_history_df

    def display(self):
        # Create main tabs
        tab_names = ["Add/Drop", "Trades"]
        tabs = st.tabs(tab_names)

        with tabs[0]:
            st.subheader("Add/Drop")
            add_drop_overview.display_add_drop(self.transaction_df, self.player_df, self.injury_df)

        with tabs[1]:
            st.subheader("Trades")
            trade_overview.display_trades(self.transaction_df, self.player_df, self.injury_df, self.draft_history_df)

# Example usage
if __name__ == "__main__":
    transaction_df = pd.DataFrame()  # Load your transaction data here
    player_df = pd.DataFrame()  # Load your player data here
    injury_df = pd.DataFrame()  # Load your injury data here
    draft_history_df = pd.DataFrame()  # Load your draft history data here
    viewer = AllTransactionsViewer(transaction_df, player_df, injury_df, draft_history_df)
    viewer.display()