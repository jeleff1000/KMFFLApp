import pandas as pd
import streamlit as st

def display_career_all_transactions(transaction_df, player_df, injury_df, draft_history_df):
    st.header("Career Transactions Overview")
    # Add your logic to display career transactions here
    st.write(transaction_df)