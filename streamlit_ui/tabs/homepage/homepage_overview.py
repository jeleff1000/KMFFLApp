import streamlit as st
from .champions import display_champions
from .season_standings import display_season_standings
from .head_to_head import display_head_to_head
from .schedules import display_schedules
from .recap_overview import display_recap_overview  # Import recap overview

def display_homepage_overview(df_dict):
    sub_tab_names = ["Champions", "Season Standings", "Schedules", "Head-to-Head", "Team Recaps"]
    sub_tabs = st.tabs(sub_tab_names)

    for i, sub_tab_name in enumerate(sub_tab_names):
        with sub_tabs[i]:
            if sub_tab_name == "Champions":
                display_champions(df_dict)
            elif sub_tab_name == "Season Standings":
                # Pass only the needed DataFrame
                display_season_standings(df_dict["Matchup Data"])
            elif sub_tab_name == "Schedules":
                display_schedules(df_dict)
            elif sub_tab_name == "Head-to-Head":
                display_head_to_head(df_dict)
            elif sub_tab_name == "Team Recaps":
                display_recap_overview(df_dict)