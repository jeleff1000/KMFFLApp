# draft_data_overview.py
import streamlit as st
import pandas as pd
from .draft_summary import display_draft_summary
from .draft_scoring_outcomes import display_scoring_outcomes
from .draft_optimizer import display_draft_optimizer
from .career_draft_stats import display_career_draft
from .draft_preferences import display_draft_preferences
from .draft_overviews import display_draft_overview  # Import your new function

def display_draft_data_overview(df_dict):
    draft_data = df_dict.get("Draft History")
    player_data = df_dict.get("Player Data")
    if draft_data is not None and player_data is not None:
        sub_tab_names = [
            "Draft Summary",
            "Scoring Outcomes",
            "Career Draft Stats",
            "Draft Optimizer",
            "Draft Preferences",
            "Average Draft Prices"  # New tab
        ]
        sub_tabs = st.tabs(sub_tab_names)
        for i, sub_tab_name in enumerate(sub_tab_names):
            with sub_tabs[i]:
                if sub_tab_name == "Draft Summary":
                    display_draft_summary(draft_data)
                elif sub_tab_name == "Scoring Outcomes":
                    display_scoring_outcomes(draft_data, player_data)
                elif sub_tab_name == "Career Draft Stats":
                    career_stats = display_career_draft(draft_data)
                    st.dataframe(career_stats)
                elif sub_tab_name == "Draft Optimizer":
                    display_draft_optimizer(draft_data, player_data)
                elif sub_tab_name == "Draft Preferences":
                    display_draft_preferences(draft_data, player_data)
                elif sub_tab_name == "Average Draft Prices":
                    display_draft_overview(draft_data)  # Call your new function
    else:
        st.error("Draft History or Player Data not found.")