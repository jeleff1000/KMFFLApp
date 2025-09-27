import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def display_player_scoring_graphs(df_dict, prefix=""):
    st.header("Player Scoring")
    player_data = df_dict.get("Player Data")
    if player_data is None or not isinstance(player_data, pd.DataFrame):
        st.error("Player Data not found.")
        return

    required_cols = {"fantasy_position", "year", "points", "manager", "player_display_name"}
    if not required_cols.issubset(player_data.columns):
        st.info("Required columns ('fantasy_position', 'year', 'points', 'manager', 'player_display_name') not found for charting.")
        return

    filtered = player_data[player_data["manager"] != "No manager"].copy()
    filtered["year"] = filtered["year"].astype(str)
    years = sorted(filtered["year"].unique())
    min_year, max_year = int(years[0]), int(years[-1])

    col1, col2 = st.columns(2)
    start_year = col1.number_input("Start Year", min_value=min_year, max_value=max_year, value=min_year, key=f"{prefix}_start_year")
    end_year = col2.number_input("End Year", min_value=min_year, max_value=max_year, value=max_year, key=f"{prefix}_end_year")

    filtered = filtered[(filtered["year"].astype(int) >= start_year) & (filtered["year"].astype(int) <= end_year)]

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

    filtered = filtered[filtered["fantasy_position"].isin(selected_positions)]

    player_search = st.text_input(
        "Enter player names (comma separated):",
        value="",
        key=f"{prefix}_player_search"
    ).strip()

    if player_search:
        search_names = [name.strip().lower() for name in player_search.split(",") if name.strip()]
        filtered["player_display_name_lower"] = filtered["player_display_name"].str.lower()
        filtered = filtered[filtered["player_display_name_lower"].isin(search_names)]
        filtered = filtered.drop(columns=["player_display_name_lower"])

    if player_search and not filtered.empty:
        fig = go.Figure()
        if start_year == end_year and "week" in filtered.columns:
            for player in filtered["player_display_name"].unique():
                player_data = filtered[filtered["player_display_name"] == player].copy()
                player_data["week"] = player_data["week"].astype(int)
                player_data = player_data.sort_values("week")
                player_data["cumulative_avg"] = player_data["points"].expanding().mean()
                player_data["week"] = player_data["week"].apply(lambda x: max(1, x))
                fig.add_trace(go.Scatter(
                    x=player_data["week"],
                    y=player_data["points"],
                    mode="markers",
                    name=f"{player} Points",
                    marker=dict(size=8),
                    hovertemplate=f"Player: {player}<br>Week: %{{x}}<br>Points: %{{y}}<extra></extra>"
                ))
                fig.add_trace(go.Scatter(
                    x=player_data["week"],
                    y=player_data["cumulative_avg"],
                    mode="lines",
                    name=f"{player} Cumulative Avg",
                    line=dict(dash="dash"),
                    hovertemplate=f"Player: {player}<br>Week: %{{x}}<br>Cumulative Avg: %{{y:.2f}}<extra></extra>"
                ))
            fig.update_layout(
                xaxis_title="Week",
                yaxis_title="Points",
                legend_title="Legend",
                title=f"Player Weekly Points and Cumulative Average ({start_year})"
            )
            fig.update_yaxes(showgrid=True)
            fig.update_xaxes(showgrid=True)
            st.subheader(f"Player Weekly Points and Cumulative Average ({start_year})")
            st.plotly_chart(fig, use_container_width=True)
        else:
            for player in filtered["player_display_name"].unique():
                player_data = filtered[filtered["player_display_name"] == player].copy()
                player_data["year"] = player_data["year"].astype(int)
                # Group by year and calculate mean points per year
                year_means = (
                    player_data.groupby("year")["points"]
                    .mean()
                    .reset_index()
                    .sort_values("year")
                )
                year_means["cumulative_avg"] = year_means["points"].expanding().mean()
                fig.add_trace(go.Scatter(
                    x=year_means["year"],
                    y=year_means["points"],
                    mode="markers",
                    name=f"{player} year Avg Points",
                    marker=dict(size=8),
                    hovertemplate=f"Player: {player}<br>year: %{{x}}<br>year Avg Points: %{{y}}<extra></extra>"
                ))
                fig.add_trace(go.Scatter(
                    x=year_means["year"],
                    y=year_means["cumulative_avg"],
                    mode="lines",
                    name=f"{player} Cumulative year Avg",
                    line=dict(dash="dash"),
                    hovertemplate=f"Player: {player}<br>year: %{{x}}<br>Cumulative year Avg: %{{y:.2f}}<extra></extra>"
                ))
            fig.update_layout(
                xaxis_title="year",
                yaxis_title="Points Per Game",
                legend_title="Legend",
                title="Player year Points and Cumulative Average"
            )
            fig.update_yaxes(showgrid=True)
            fig.update_xaxes(showgrid=True, tickmode='linear', dtick=1)
            st.subheader("Player year Points and Cumulative Average")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Enter at least one player name to display the graph.")