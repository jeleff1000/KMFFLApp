import streamlit as st
import pandas as pd

class SeasonInjuryStatsViewer:
    def __init__(self):
        pass

    def display(self, merged_data):
        st.header("Season Injury Stats")

        # Ensure all values in the player, owner, and report_status columns are strings
        merged_data["player"] = merged_data["player"].astype(str)
        merged_data["owner"] = merged_data["owner"].astype(str)
        merged_data["report_status"] = merged_data["report_status"].astype(str)

        # Create columns for player and owner search bars
        col1, col2 = st.columns(2)
        with col1:
            players = st.multiselect("Search by Player", options=sorted(merged_data["player"].unique()), key="player_multiselect")
        with col2:
            owners = st.multiselect("Search by Owner", options=sorted(merged_data["owner"].unique()), key="owner_multiselect")

        # Create columns for season and report status dropdowns
        col3, col4 = st.columns(2)
        with col3:
            seasons = sorted(merged_data["season"].unique())
            season = st.multiselect("Select Season", options=["All"] + list(seasons), key="season_multiselect")
        with col4:
            report_statuses = sorted(merged_data["report_status"].unique())
            report_status = st.multiselect("Select Report Status", options=["All"] + list(report_statuses), key="report_status_multiselect")

        # Filter the dataframe based on the search inputs
        filtered_data = merged_data[
            (merged_data["player"].isin(players) if players else merged_data["player"].notna()) &
            (merged_data["owner"].isin(owners) if owners else merged_data["owner"].notna()) &
            ((merged_data["season"].isin(season)) if season and "All" not in season else merged_data["season"].notna()) &
            ((merged_data["report_status"].isin(report_status)) if report_status and "All" not in report_status else merged_data["report_status"].notna())
        ]

        # Aggregate the data by player and season
        aggregated_data = filtered_data.pivot_table(
            index=["player", "season"],
            columns="report_status",
            aggfunc="size",
            fill_value=0
        ).reset_index()

        # Ensure all possible report statuses are present
        for status in ["Questionable", "Doubtful", "Out"]:
            if status not in aggregated_data.columns:
                aggregated_data[status] = 0

        # Rename the columns for clarity
        aggregated_data.columns = ["player", "season"] + list(aggregated_data.columns[2:])

        # Merge with other required columns
        additional_columns = filtered_data.groupby(["player", "season"]).agg({
            "team_y": "first",
            "owner": "first",
            "position_y": "first"
        }).reset_index()

        aggregated_data = pd.merge(aggregated_data, additional_columns, on=["player", "season"])

        # Select the specified columns
        columns_to_display = [
            "season", "player", "team_y", "owner", "position_y",
            "Questionable", "Doubtful", "Out"
        ]
        aggregated_data = aggregated_data[columns_to_display]

        # Format the season column to remove commas
        aggregated_data["season"] = aggregated_data["season"].astype(str)

        # Display the aggregated dataframe without the index
        st.dataframe(aggregated_data, hide_index=True)