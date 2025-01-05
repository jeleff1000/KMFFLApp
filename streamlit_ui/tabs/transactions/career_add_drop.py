import pandas as pd
import streamlit as st
from .season_add_drop import display_season_add_drop

def display_career_add_drop(transaction_df, player_df):
    # Get the season aggregated DataFrame
    season_aggregated_df = display_season_add_drop(transaction_df, player_df, return_df=True)

    # Group by manager and aggregate the necessary columns for career view
    career_aggregated_df = season_aggregated_df.groupby(['manager']).agg({
        'faab': 'sum',
        'add_pts_to_date': 'sum',
        'add_pts_ROS': 'sum',
        'drop_pts_to_date': 'sum',
        'drop_pts_ROS': 'sum',
        'points_gained': 'sum',
        'transaction_count': 'sum'
    }).reset_index()

    # Add search bar for manager
    nickname_search = st.text_input('Search by Manager', key='nickname_search_career')

    # Filter the DataFrame based on search input
    if nickname_search:
        career_aggregated_df = career_aggregated_df[career_aggregated_df['manager'].str.contains(nickname_search, case=False, na=False)]

    # Display the merged data in a table without the index
    st.dataframe(career_aggregated_df, hide_index=True)