import streamlit as st
from tabs.homepage.champions import display_champions
from tabs.homepage.season_standings import display_season_standings
from tabs.homepage.head_to_head import display_head_to_head
from tabs.homepage.schedules import display_schedules  # Import the schedules tab

def display_homepage_overview(df_dict):
    sub_tab_names = ["Champions", "Season Standings", "Schedules", "Head-to-Head"]
    sub_tabs = st.tabs(sub_tab_names)

    for i, sub_tab_name in enumerate(sub_tab_names):
        with sub_tabs[i]:
            if sub_tab_name == "Champions":
                display_champions(df_dict)
            elif sub_tab_name == "Season Standings":
                display_season_standings(df_dict)
            elif sub_tab_name == "Schedules":
                display_schedules(df_dict)
            elif sub_tab_name == "Head-to-Head":
                display_head_to_head(df_dict)