# draft_data_overview.py
import streamlit as st
import pandas as pd
from .draft_summary import display_draft_summary  # Import the display_draft_summary function
from .draft_scoring_outcomes import display_scoring_outcomes  # Import the display_scoring_outcomes function
from .draft_optimizer import display_draft_optimizer  # Import the display_draft_optimizer function

def display_draft_data_overview(df_dict):
    draft_data = df_dict.get("Draft History")
    player_data = df_dict.get("Player Data")
    if draft_data is not None and player_data is not None:
        sub_tab_names = ["Draft Summary", "Draft Optimizer", "Scoring Outcomes"]
        sub_tabs = st.tabs(sub_tab_names)
        for i, sub_tab_name in enumerate(sub_tab_names):
            with sub_tabs[i]:
                if sub_tab_name == "Draft Summary":
                    display_draft_summary(draft_data)
                elif sub_tab_name == "Draft Optimizer":
                    display_draft_optimizer(draft_data, player_data)  # Pass both draft_data and player_data
                elif sub_tab_name == "Scoring Outcomes":
                    display_scoring_outcomes(draft_data, player_data)
    else:
        st.error("Draft History or Player Data not found.")