# draft_data_overview.py
import streamlit as st
import pandas as pd

def display_draft_data_overview(df_dict):
    # Lazy imports so one failing submodule doesn't prevent this function from existing
    try:
        from .draft_summary import display_draft_summary
    except Exception as e:
        display_draft_summary = None
        st.error(f"Failed to load Draft Summary view: {e}")

    try:
        from .draft_scoring_outcomes import display_scoring_outcomes
    except Exception as e:
        display_scoring_outcomes = None
        st.error(f"Failed to load Scoring Outcomes view: {e}")

    try:
        from .draft_optimizer import display_draft_optimizer
    except Exception as e:
        display_draft_optimizer = None
        st.error(f"Failed to load Draft Optimizer view: {e}")

    try:
        from .career_draft_stats import display_career_draft
    except Exception as e:
        display_career_draft = None
        st.error(f"Failed to load Career Draft Stats view: {e}")

    try:
        from .draft_preferences import display_draft_preferences
    except Exception as e:
        display_draft_preferences = None
        st.error(f"Failed to load Draft Preferences view: {e}")

    try:
        # Make sure the file is exactly named draft_overviews.py (case-sensitive on Linux)
        from .draft_overviews import display_draft_overview
    except Exception as e:
        display_draft_overview = None
        st.error(f"Failed to load Average Draft Prices view: {e}")

    draft_data = df_dict.get("Draft History")
    player_data = df_dict.get("Player Data")
    if draft_data is None or player_data is None:
        st.error("Draft History or Player Data not found.")
        return

    sub_tab_names = [
        "Draft Summary",
        "Scoring Outcomes",
        "Career Draft Stats",
        "Draft Optimizer",
        "Draft Preferences",
        "Average Draft Prices",
    ]
    sub_tabs = st.tabs(sub_tab_names)

    with sub_tabs[0]:
        if display_draft_summary:
            display_draft_summary(draft_data)

    with sub_tabs[1]:
        if display_scoring_outcomes:
            display_scoring_outcomes(draft_data, player_data)

    with sub_tabs[2]:
        if display_career_draft:
            career_stats = display_career_draft(draft_data)
            if isinstance(career_stats, pd.DataFrame):
                st.dataframe(career_stats)

    with sub_tabs[3]:
        if display_draft_optimizer:
            display_draft_optimizer(draft_data, player_data)

    with sub_tabs[4]:
        if display_draft_preferences:
            display_draft_preferences(draft_data, player_data)

    with sub_tabs[5]:
        if display_draft_overview:
            # If your function needs different args, adjust here
            display_draft_overview(draft_data)
