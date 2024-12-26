import streamlit as st
import pandas as pd
import pickle
from UI_Tabs.Matchup_Data import MatchupDataViewer

# Function to load the pickle file
def load_pickle_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            df_dict = pickle.load(f)
        return df_dict
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return None

# Main function
def main():
    st.title("KMFFL App")

    # Load the pickle file
    file_path = r'C:\Users\joeye\OneDrive\Desktop\kmffl\Adin\Scripts\Sheet 2.0\Sheet 2.0\Sheet 2.0.pkl'
    df_dict = load_pickle_file(file_path)

    if df_dict:
        # Create tabs
        tabs = st.tabs(["Matchup Data", "Player Data", "Draft History", "All Transactions", "Adds", "Drops", "Trades", "Injuries", "Simulations"])

        with tabs[0]:
            matchup_data_viewer = MatchupDataViewer(df_dict.get("Matchup Data"))
            matchup_data_viewer.display()
        with tabs[1]:
            st.header("Player Data")
            st.dataframe(df_dict.get("Player Data"))
        with tabs[2]:
            st.header("Draft History")
            st.dataframe(df_dict.get("Draft History"))
        with tabs[3]:
            st.header("All Transactions")
            st.dataframe(df_dict.get("All Transactions"))
        with tabs[4]:
            st.header("Adds")
            st.dataframe(df_dict.get("Adds"))
        with tabs[5]:
            st.header("Drops")
            st.dataframe(df_dict.get("Drops"))
        with tabs[6]:
            st.header("Trades")
            st.dataframe(df_dict.get("Trades"))
        with tabs[7]:
            st.header("Injuries")
            st.dataframe(df_dict.get("Injuries"))
        with tabs[8]:
            st.header("Simulations")
            st.write("Simulations content goes here")

if __name__ == "__main__":
    main()