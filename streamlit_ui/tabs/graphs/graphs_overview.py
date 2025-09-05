import streamlit as st
from .weekly_scoring_graphs import display_weekly_scoring_graphs
from .draft_preferences_graph import display_cost_over_time_graph
from .position_group_scoring import display_position_group_scoring_graphs

def display_graphs_overview(df_dict):
    st.title("Graphs Overview")
    st.write("Select a graph tab below to view details.")

    tab_names = [
        "Weekly Scoring",
        "Draft Preferences",
        "Position Group Scoring",
        # Add more tab names here
    ]
    tabs = st.tabs(tab_names)

    for i, tab_name in enumerate(tab_names):
        with tabs[i]:
            unique_prefix = f"graphs_{tab_name.lower().replace(' ', '_')}_{i}"
            if tab_name == "Weekly Scoring":
                display_weekly_scoring_graphs(df_dict, prefix=unique_prefix)
            elif tab_name == "Draft Preferences":
                draft_data = df_dict.get("Draft History")
                if draft_data is not None:
                    display_cost_over_time_graph(draft_data, unique_prefix=unique_prefix)
                else:
                    st.error("Draft data not found.")
            elif tab_name == "Position Group Scoring":
                display_position_group_scoring_graphs(df_dict, prefix=unique_prefix)
            else:
                st.info("No content for this tab yet.")