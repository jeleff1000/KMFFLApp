import streamlit as st
from .weekly_scoring_graphs import display_weekly_scoring_graphs
from .all_time_scoring_graphs import display_all_time_scoring_graphs
from .win_loss_graph import display_win_loss_graph
from .draft_preferences_graph import display_cost_over_time_graph
from .position_group_scoring import display_position_group_scoring_graphs
from .player_scoring_graph import display_player_scoring_graphs
from .playoff_odds_graph import PlayoffOddsViewer
from .yearly_playoff_graph import PlayoffOddsCumulativeViewer  # New import
from .power_rating import display_power_rating_graph  # <-- NEW

def display_graphs_overview(df_dict):
    st.title("Graphs Overview")
    st.write("Select a graph tab below to view details.")

    top_tab_names = [
        "Manager Graphs",
        "Player Graphs",
        "Draft Graphs",
        "Playoff Odds",
    ]
    top_tabs = st.tabs(top_tab_names)

    # Manager Graphs: Weekly, All-Time, Win/Loss, Power Rating
    with top_tabs[0]:
        m_sub_names = ["Weekly Scoring", "All-Time Scoring", "Win Loss Graph", "Power Rating"]
        m_sub_tabs = st.tabs(m_sub_names)
        for i, name in enumerate(m_sub_names):
            with m_sub_tabs[i]:
                prefix = f"graphs_manager_{name.lower().replace(' ', '_')}_{i}"
                if name == "Weekly Scoring":
                    display_weekly_scoring_graphs(df_dict, prefix=prefix)
                elif name == "All-Time Scoring":
                    display_all_time_scoring_graphs(df_dict, prefix=prefix)
                elif name == "Win Loss Graph":
                    display_win_loss_graph(df_dict, prefix=prefix)
                elif name == "Power Rating":
                    display_power_rating_graph(df_dict, prefix=prefix)

    # Player Graphs: Position Group, Player
    with top_tabs[1]:
        p_sub_names = ["Position Group Scoring", "Player Scoring"]
        p_sub_tabs = st.tabs(p_sub_names)
        for i, name in enumerate(p_sub_names):
            with p_sub_tabs[i]:
                prefix = f"graphs_player_{name.lower().replace(' ', '_')}_{i}"
                if name == "Position Group Scoring":
                    display_position_group_scoring_graphs(df_dict, prefix=prefix)
                elif name == "Player Scoring":
                    display_player_scoring_graphs(df_dict, prefix=prefix)

    # Draft Graphs: Draft Preferences
    with top_tabs[2]:
        d_sub_names = ["Draft Preferences"]
        d_sub_tabs = st.tabs(d_sub_names)
        for i, name in enumerate(d_sub_names):
            with d_sub_tabs[i]:
                prefix = f"graphs_draft_{name.lower().replace(' ', '_')}_{i}"
                draft_data = df_dict.get("Draft History")
                if draft_data is not None:
                    display_cost_over_time_graph(draft_data, unique_prefix=prefix)
                else:
                    st.error("Draft data not found.")

    # Playoff Odds: Weekly and Cumulative Week subtabs
    with top_tabs[3]:
        matchup_data = df_dict.get("Matchup Data")
        if matchup_data is None:
            st.error("Matchup data not found.")
        else:
            po_tab_names = ["Weekly", "Cumulative Week"]
            po_tabs = st.tabs(po_tab_names)

            with po_tabs[0]:
                PlayoffOddsViewer(matchup_data).display()

            with po_tabs[1]:
                PlayoffOddsCumulativeViewer(matchup_data).display()