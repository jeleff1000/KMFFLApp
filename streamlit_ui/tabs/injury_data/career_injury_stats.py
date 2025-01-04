import streamlit as st
import pandas as pd

class CareerInjuryStatsViewer:
    def __init__(self):
        pass

    def display(self, merged_data):
        st.header("Career Injury Stats")

        # Ensure all values in the player, position_y, owner, and report_status columns are strings
        merged_data["player"] = merged_data["player"].astype(str)
        merged_data["position_y"] = merged_data["position_y"].astype(str)
        merged_data["owner"] = merged_data["owner"].astype(str)
        merged_data["report_status"] = merged_data["report_status"].astype(str)

        # Create columns for player and owner search bars
        col1, col2 = st.columns(2)
        with col1:
            players = st.multiselect("Search by Player", options=sorted(merged_data["player"].unique()), key="career_player_multiselect")
        with col2:
            owner_search = st.text_input("Search by Owner", key="career_owner_search")

        # Create columns for report status dropdown
        report_statuses = sorted(merged_data["report_status"].unique())
        report_status = st.multiselect("Select Report Status", options=["All"] + list(report_statuses), key="career_report_status_multiselect")

        # Filter the dataframe based on the search inputs
        filtered_data = merged_data[
            (merged_data["player"].isin(players) if players else merged_data["player"].notna()) &
            (merged_data["owner"].str.contains(owner_search, case=False) if owner_search else merged_data["owner"].notna()) &
            ((merged_data["report_status"].isin(report_status)) if report_status and "All" not in report_status else merged_data["report_status"].notna())
        ]

        # Aggregate the data by player and position_y
        aggregated_data = filtered_data.pivot_table(
            index=["player", "position_y"],
            columns="report_status",
            aggfunc="size",
            fill_value=0
        ).reset_index()

        # Ensure all possible report statuses are present
        for status in ["Questionable", "Doubtful", "Out"]:
            if status not in aggregated_data.columns:
                aggregated_data[status] = 0

        # Rename the columns for clarity
        aggregated_data.columns = ["player", "position_y"] + list(aggregated_data.columns[2:])

        # Select the specified columns
        columns_to_display = [
            "player", "position_y", "Questionable", "Doubtful", "Out"
        ]
        aggregated_data = aggregated_data[columns_to_display]

        # Display the aggregated dataframe without the index
        st.dataframe(aggregated_data, hide_index=True)