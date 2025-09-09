import streamlit as st
from .weekly_scoring_graphs import display_weekly_scoring_graphs
from .all_time_scoring_graphs import display_all_time_scoring_graphs
from .win_loss_graph import display_win_loss_graph  # <-- Import here
from .draft_preferences_graph import display_cost_over_time_graph
from .position_group_scoring import display_position_group_scoring_graphs
from .player_scoring_graph import display_player_scoring_graphs
from .playoff_odds_graph import PlayoffOddsViewer

def display_graphs_overview(df_dict):
    st.title("Graphs Overview")
    st.write("Select a graph tab below to view details.")

    tab_names = [
        "Weekly Scoring",
        "All-Time Scoring",
        "Win Loss Graph",  # <-- Add here
        "Draft Preferences",
        "Position Group Scoring",
        "Player Scoring",
        "Playoff Odds",
    ]
    tabs = st.tabs(tab_names)

    for i, tab_name in enumerate(tab_names):
        with tabs[i]:
            unique_prefix = f"graphs_{tab_name.lower().replace(' ', '_')}_{i}"
            if tab_name == "Weekly Scoring":
                display_weekly_scoring_graphs(df_dict, prefix=unique_prefix)
            elif tab_name == "All-Time Scoring":
                display_all_time_scoring_graphs(df_dict, prefix=unique_prefix)
            elif tab_name == "Win Loss Graph":  # <-- Add logic here
                display_win_loss_graph(df_dict, prefix=unique_prefix)
            elif tab_name == "Draft Preferences":
                draft_data = df_dict.get("Draft History")
                if draft_data is not None:
                    display_cost_over_time_graph(draft_data, unique_prefix=unique_prefix)
                else:
                    st.error("Draft data not found.")
            elif tab_name == "Position Group Scoring":
                display_position_group_scoring_graphs(df_dict, prefix=unique_prefix)
            elif tab_name == "Player Scoring":
                display_player_scoring_graphs(df_dict, prefix=unique_prefix)
            elif tab_name == "Playoff Odds":
                matchup_data = df_dict.get("Matchup Data")
                if matchup_data is not None:
                    PlayoffOddsViewer(matchup_data).display()
                else:
                    st.error("Matchup data not found.")
            else:
                st.info("No content for this tab yet.")