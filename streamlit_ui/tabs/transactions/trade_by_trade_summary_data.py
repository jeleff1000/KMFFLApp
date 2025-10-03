import pandas as pd
import streamlit as st

def display_trade_by_trade_summary_data(transaction_df, player_df, draft_history_df):
    transaction_df = transaction_df.rename(columns={
        "name": "player_name",
        "nickname": "manager"
    })
    draft_history_df = draft_history_df.rename(columns={
        "Name Full": "player_name",
        "Year": "year",
        "Cost": "cost",
        "Is Keeper Status": "is_keeper_status",
    })

    transaction_df["manager"] = transaction_df["manager"].fillna("Unknown")
    transaction_df.drop_duplicates(subset=["transaction_id", "player_name"], inplace=True)
    trade_transactions = transaction_df[transaction_df["transaction_type"] == "trade"]
    player_df.drop_duplicates(subset=["player", "week", "year"], inplace=True)
    draft_history_df.drop_duplicates(subset=["player_name", "year"], inplace=True)

    trade_transactions = pd.merge(
        trade_transactions,
        draft_history_df[["player_name", "year", "cost", "is_keeper_status"]],
        on=["player_name", "year"],
        how="left",
    )

    # Use yahoo_position instead of position
    merged_df = pd.merge(
        trade_transactions[
            ["transaction_id", "player_name", "week", "year", "transaction_type", "faab_bid", "manager", "cost", "is_keeper_status"]
        ],
        player_df[["player", "week", "year", "rolling_point_total", "yahoo_position"]],
        left_on=["player_name", "week", "year"],
        right_on=["player", "week", "year"],
        how="left",
    )

    merged_df["manager"] = merged_df["manager"].fillna("Unknown")
    points_transaction_week = player_df.set_index(["player", "year", "week"])["rolling_point_total"]
    merged_df["points_transaction_week"] = (
        merged_df.set_index(["player_name", "year", "week"]).index.map(points_transaction_week).fillna(0).values
    )

    max_week_up_to_16 = (
        player_df[(player_df["week"] <= 16) & (player_df["year"] <= 2020)]
        .groupby(["player", "year"])["week"]
        .idxmax()
    )
    max_week_up_to_17 = (
        player_df[(player_df["week"] <= 17) & (player_df["year"] >= 2021)]
        .groupby(["player", "year"])["week"]
        .idxmax()
    )
    points_max_week_up_to_16 = player_df.loc[max_week_up_to_16].set_index(["player", "year"])["rolling_point_total"]
    points_max_week_up_to_17 = player_df.loc[max_week_up_to_17].set_index(["player", "year"])["rolling_point_total"]

    merged_df["points_week_max"] = merged_df.apply(
        lambda row: points_max_week_up_to_16.get((row["player_name"], row["year"]), 0)
        if row["year"] <= 2020
        else points_max_week_up_to_17.get((row["player_name"], row["year"]), 0),
        axis=1,
    )
    merged_df["points_week_max"] -= merged_df["points_transaction_week"]

    # Use yahoo_position for ranking
    merged_df["ros_rank"] = merged_df.groupby("yahoo_position")["points_week_max"].rank(ascending=False, method="min")
    merged_df["ros_rank"] = merged_df["ros_rank"].fillna(0).astype(int)
    merged_df["ros_rank"] = merged_df["yahoo_position"] + merged_df["ros_rank"].astype(str)

    merged_df.rename(columns={"faab_bid": "faab"}, inplace=True)
    merged_df["is_keeper"] = merged_df["is_keeper_status"]

    def sort_names_ranks(names, ranks):
        def num_from_rank(s):
            digits = "".join(ch for ch in s if ch.isdigit())
            return int(digits) if digits else 0
        combined = list(zip(names, ranks))
        combined.sort(key=lambda x: num_from_rank(x[1]))
        sorted_names, sorted_ranks = zip(*combined) if combined else ([], [])
        return ", ".join(sorted_names), ", ".join(sorted_ranks)

    aggregated_df = merged_df.groupby(["transaction_id", "manager"]).agg({
        "week": "first",
        "year": "first",
        "player_name": lambda x: ", ".join(x),
        "points_transaction_week": "sum",
        "points_week_max": "sum",
        "cost": "sum",
        "is_keeper": "sum",
        "ros_rank": lambda x: ", ".join(x.astype(str)),
    }).reset_index()

    aggregated_df[["player_name", "ros_rank"]] = aggregated_df.apply(
        lambda row: sort_names_ranks(row["player_name"].split(", "), row["ros_rank"].split(", ")),
        axis=1, result_type="expand"
    )

    traded_away_df = merged_df.copy().rename(columns={
        "player_name": "traded_away_name",
        "points_transaction_week": "traded_away_points_transaction_week",
        "points_week_max": "traded_away_points_week_max",
        "cost": "traded_away_cost",
        "is_keeper": "traded_away_is_keeper",
        "ros_rank": "traded_away_ros_rank",
    })

    traded_away_aggregated_df = traded_away_df.groupby(["transaction_id", "manager"]).agg({
        "traded_away_name": lambda x: ", ".join(x),
        "traded_away_points_transaction_week": "sum",
        "traded_away_points_week_max": "sum",
        "traded_away_cost": "sum",
        "traded_away_is_keeper": "sum",
        "traded_away_ros_rank": lambda x: ", ".join(x.astype(str)),
    }).reset_index()

    traded_away_aggregated_df[["traded_away_name", "traded_away_ros_rank"]] = traded_away_aggregated_df.apply(
        lambda row: sort_names_ranks(row["traded_away_name"].split(", "), row["traded_away_ros_rank"].split(", ")),
        axis=1, result_type="expand"
    )

    final_df = pd.merge(aggregated_df, traded_away_aggregated_df, on="transaction_id", suffixes=("", "_away"))
    final_df = final_df[final_df["manager"] != final_df["manager_away"]]
    final_df["points_gained_in_trade"] = final_df["points_week_max"] - final_df["traded_away_points_week_max"]
    final_df["trade_partner"] = final_df["manager_away"]
    final_df["year"] = final_df["year"].astype(int).astype(str)
    final_df.drop_duplicates(inplace=True)

    final_df = final_df[[
        "manager", "trade_partner", "week", "year",
        "player_name", "ros_rank",
        "traded_away_name", "traded_away_ros_rank",
        "is_keeper", "points_gained_in_trade",
        "points_transaction_week", "points_week_max",
        "traded_away_points_transaction_week", "traded_away_points_week_max",
        "traded_away_cost", "traded_away_is_keeper",
        "cost", "transaction_id",
    ]]

    final_df.rename(columns={
        "transaction_id": "id",
        "manager": "mngr",
        "trade_partner": "prtnr",
        "week": "wk",
        "year": "yr",
        "player_name": "acquired",
        "ros_rank": "acquired_rank",
        "traded_away_name": "traded_away",
        "traded_away_ros_rank": "traded_away_rank",
        "points_gained_in_trade": "pts_gained",
        "is_keeper": "nxt_yr_keeper",
        "points_transaction_week": "acqrd_pre_trade_pts",
        "points_week_max": "acqrd_pts_post_trade",
        "cost": "next_yr_draft_price",
        "traded_away_points_transaction_week": "traded_away_pts_pre_trade",
        "traded_away_points_week_max": "traded_away_pts_post_trade",
        "traded_away_cost": "traded_away_price_next_year",
        "traded_away_is_keeper": "traded_away_keeper",
    }, inplace=True)

    st.session_state["trade_summary_df"] = final_df

    col1, col2, col3 = st.columns(3)
    with col1:
        year_search = st.selectbox(
            "Search by Year", options=["All"] + list(final_df["yr"].unique()),
            key="year_search_trades_summary"
        )
    with col2:
        name_search = st.text_input("Search by Player Name", key="player_search_trades_summary")
    with col3:
        nickname_search = st.text_input("Search by Manager", key="nickname_search_trades_summary")

    filtered_df = final_df.copy()
    if year_search and year_search != "All":
        filtered_df = filtered_df[filtered_df["yr"] == year_search]
    if nickname_search:
        filtered_df = filtered_df[filtered_df["mngr"].str.contains(nickname_search, case=False, na=False)]
    if name_search:
        filtered_df = filtered_df[filtered_df["acquired"].str.contains(name_search, case=False, na=False)]

    st.dataframe(filtered_df, hide_index=True)