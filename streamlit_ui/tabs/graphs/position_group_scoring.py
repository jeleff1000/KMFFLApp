import streamlit as st
import pandas as pd

def display_position_group_scoring_graphs(df_dict, prefix=""):
    st.header("Position Group Scoring")
    player_data = df_dict.get("Player Data")
    if player_data is None or not isinstance(player_data, pd.DataFrame):
        st.error("Player Data not found.")
        return

    required_cols = {"fantasy_position", "year", "points", "manager"}
    if required_cols.issubset(player_data.columns):
        filtered = player_data[player_data["manager"] != "No manager"].copy()
        filtered["year"] = filtered["year"].astype(str)

        # Manager dropdown only
        managers = sorted(filtered["manager"].unique())
        manager = st.selectbox("Select Manager", ["All Managers"] + managers, key=f"{prefix}_manager")
        if manager != "All Managers":
            filtered = filtered[filtered["manager"] == manager]

        # Fixed position order
        position_order = ["QB", "RB", "WR", "TE", "W/R/T", "DEF", "K", "BN", "IR"]
        available_positions = [pos for pos in position_order if pos in filtered["fantasy_position"].unique()]
        default_positions = [pos for pos in available_positions if pos not in {"BN", "IR"}]

        with st.expander("Select Positions to Display", expanded=True):
            selected_positions = []
            cols = st.columns(len(available_positions))
            for i, pos in enumerate(available_positions):
                default = pos in default_positions
                checked = cols[i].checkbox(pos, value=default, key=f"{prefix}_pos_{pos}")
                if checked:
                    selected_positions.append(pos)

        if selected_positions:
            filtered = filtered[filtered["fantasy_position"].isin(selected_positions)]
            grouped = (
                filtered
                .groupby(["fantasy_position", "year"])["points"]
                .mean()
                .reset_index()
            )
            grouped["points"] = grouped["points"].round(2)
            pivoted = grouped.pivot(index="year", columns="fantasy_position", values="points")
            pivoted = pivoted[[pos for pos in position_order if pos in pivoted.columns]]
            pivoted = pivoted.round(2)
            st.subheader("Average Points Per Game by fantasy_position and year")
            st.line_chart(pivoted)
        else:
            st.info("No positions selected.")
    else:
        st.info("Required columns ('fantasy_position', 'year', 'points', 'manager') not found for charting.")