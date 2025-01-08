# streamlit_ui/tabs/matchup_data_and_simulations/matchups/matchup_overview.py

from .weekly.weekly_matchup_overview import WeeklyMatchupDataViewer
from .season.season_matchup_overview import SeasonMatchupOverviewViewer
from .all_time.career_matchup_overview import CareerMatchupOverviewViewer

def display_matchup_overview(df_dict, prefix=""):
    import streamlit as st

    sub_tab_names = ["Weekly", "Seasons", "Career"]
    sub_tabs = st.tabs(sub_tab_names)
    for j, sub_tab_name in enumerate(sub_tab_names):
        with sub_tabs[j]:
            matchup_data = df_dict.get("Matchup Data")
            player_data = df_dict.get("Player Data")
            if matchup_data is not None and player_data is not None:
                if sub_tab_name == "Weekly":
                    matchup_data_viewer = WeeklyMatchupDataViewer(matchup_data, player_data)
                    matchup_data_viewer.display(prefix=f"{prefix}_weekly_matchup_data")
                elif sub_tab_name == "Seasons":
                    matchup_data_viewer = SeasonMatchupOverviewViewer(matchup_data, player_data)
                    matchup_data_viewer.display(prefix=f"{prefix}_season_matchup_data")
                elif sub_tab_name == "Career":
                    career_matchup_viewer = CareerMatchupOverviewViewer(matchup_data, player_data)
                    career_matchup_viewer.display(prefix=f"{prefix}_career_matchup_data")
            else:
                st.error(f"{sub_tab_name} Matchup Data or Player Data not found.")