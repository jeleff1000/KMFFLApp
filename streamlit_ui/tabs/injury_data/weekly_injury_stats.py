import streamlit as st

class WeeklyInjuryStatsViewer:
    def __init__(self):
        pass

    def display(self, merged_data):
        st.header("Weekly Injury Stats")

        required_columns = ["player", "manager", "report_status", "year"]
        missing_columns = [col for col in required_columns if col not in merged_data.columns]

        if missing_columns:
            st.error(f"Missing columns in data: {', '.join(missing_columns)}")
            return

        # Ensure all values in the player, manager, and report_status columns are strings
        merged_data["player"] = merged_data["player"].astype(str)
        merged_data["manager"] = merged_data["manager"].astype(str)
        merged_data["report_status"] = merged_data["report_status"].astype(str)

        # Create columns for player and manager search bars
        col1, col2 = st.columns(2)
        with col1:
            players = st.multiselect("Search by Player", options=sorted(merged_data["player"].unique()))
        with col2:
            managers = st.multiselect("Search by manager", options=sorted(merged_data["manager"].unique()))

        # Create columns for year and report status dropdowns
        col3, col4 = st.columns(2)
        with col3:
            years = sorted(merged_data["year"].unique())
            year = st.multiselect("Select year", options=["All"] + list(years))
        with col4:
            report_statuses = sorted(merged_data["report_status"].unique())
            report_status = st.multiselect("Select Report Status", options=["All"] + list(report_statuses))

        # Filter the dataframe based on the search inputs
        filtered_data = merged_data[
            (merged_data["player"].isin(players) if players else merged_data["player"].notna()) &
            (merged_data["manager"].isin(managers) if managers else merged_data["manager"].notna()) &
            ((merged_data["year"].isin(year)) if year and "All" not in year else merged_data["year"].notna()) &
            ((merged_data["report_status"].isin(report_status)) if report_status and "All" not in report_status else merged_data["report_status"].notna())
        ]

        # Select the specified columns
        columns_to_display = [
            "week", "year", "nfl_team", "player", "manager", "position_y",
            "fantasy_position", "report_primary_injury", "report_secondary_injury",
            "report_status", "practice_status"
        ]
        filtered_data = filtered_data[columns_to_display]

        # Format the year column to remove commas
        filtered_data["year"] = filtered_data["year"].astype(str)

        # Display the filtered dataframe without the index
        st.dataframe(filtered_data, hide_index=True)