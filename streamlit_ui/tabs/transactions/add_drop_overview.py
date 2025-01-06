import pandas as pd
import streamlit as st
from .weekly_add_drop import display_weekly_add_drop
from .season_add_drop import display_season_add_drop
from .career_add_drop import display_career_add_drop

def display_add_drop(transaction_df, player_df, injury_df):
    # Create specific tabs for Add/Drop
    sub_tab_names = ["Weekly", "Season", "Career"]
    sub_tabs = st.tabs(sub_tab_names)

    for i, sub_tab_name in enumerate(sub_tab_names):
        with sub_tabs[i]:
            st.subheader(sub_tab_name)
            if sub_tab_name == "Weekly":
                # Define unique keys for Weekly tab
                add_drop_keys = {
                    'year_search': 'year_search_add_drop',
                    'added_player_search': 'added_player_search_add_drop',
                    'nickname_search': 'nickname_search_add_drop',
                    'dropped_player_search': 'dropped_player_search_add_drop',
                    'added_position_search': 'added_position_search_add_drop',
                    'dropped_position_search': 'dropped_position_search_add_drop'
                }
                display_weekly_add_drop(transaction_df, player_df, add_drop_keys)
            elif sub_tab_name == "Season":
                display_season_add_drop(transaction_df, player_df)
            elif sub_tab_name == "Career":
                display_career_add_drop(transaction_df, player_df)
            else:
                # Placeholder for Career data
                st.write(f"{sub_tab_name} Add/Drop data will be displayed here.")