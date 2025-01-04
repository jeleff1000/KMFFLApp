import streamlit as st

class WeeklyInjuryStatsViewer:
    def __init__(self):
        pass

    def display(self, merged_data):
        st.header("Weekly Injury Stats")

        required_columns = ["player", "owner", "report_status", "season"]
        missing_columns = [col for col in required_columns if col not in merged_data.columns]

        if missing_columns:
            st.error(f"Missing columns in data: {', '.join(missing_columns)}")
            return

        # Ensure all values in the player, owner, and report_status columns are strings
        merged_data["player"] = merged_data["player"].astype(str)
        merged_data["owner"] = merged_data["owner"].astype(str)
        merged_data["report_status"] = merged_data["report_status"].astype(str)

        # Create columns for player and owner search bars
        col1, col2 = st.columns(2)
        with col1:
            players = st.multiselect("Search by Player", options=sorted(merged_data["player"].unique()))
        with col2:
            owners = st.multiselect("Search by Owner", options=sorted(merged_data["owner"].unique()))

        # Create columns for season and report status dropdowns
        col3, col4 = st.columns(2)
        with col3:
            seasons = sorted(merged_data["season"].unique())
            season = st.multiselect("Select Season", options=["All"] + list(seasons))
        with col4:
            report_statuses = sorted(merged_data["report_status"].unique())
            report_status = st.multiselect("Select Report Status", options=["All"] + list(report_statuses))

        # Filter the dataframe based on the search inputs
        filtered_data = merged_data[
            (merged_data["player"].isin(players) if players else merged_data["player"].notna()) &
            (merged_data["owner"].isin(owners) if owners else merged_data["owner"].notna()) &
            ((merged_data["season"].isin(season)) if season and "All" not in season else merged_data["season"].notna()) &
            ((merged_data["report_status"].isin(report_status)) if report_status and "All" not in report_status else merged_data["report_status"].notna())
        ]

        # Select the specified columns
        columns_to_display = [
            "week", "season", "team_y", "player", "owner", "position_y",
            "fantasy position", "report_primary_injury", "report_secondary_injury",
            "report_status", "practice_status"
        ]
        filtered_data = filtered_data[columns_to_display]

        # Format the season column to remove commas
        filtered_data["season"] = filtered_data["season"].astype(str)

        # Display the filtered dataframe without the index
        st.dataframe(filtered_data, hide_index=True)