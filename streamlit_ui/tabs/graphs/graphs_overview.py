# python
import streamlit as st
from .weekly_scoring_graphs import display_weekly_scoring_graphs

def display_graphs_overview(df_dict):
    st.title("Graphs Overview")
    st.write("Select a graph tab below to view details.")

    tab_names = [
        "Cumulative Team Points by Week",
        "Weekly Scoring",
        # Add more tab names here
    ]
    tabs = st.tabs(tab_names)

    for i, tab_name in enumerate(tab_names):
        with tabs[i]:
            unique_prefix = f"graphs_{tab_name.lower().replace(' ', '_')}_{i}"
            if tab_name == "Cumulative Team Points by Week":
                st.info("Cumulative Team Points by Week graph is not implemented in this file.")
            elif tab_name == "Weekly Scoring":
                display_weekly_scoring_graphs(df_dict, prefix=unique_prefix)
            else:
                st.info("No content for this tab yet.")