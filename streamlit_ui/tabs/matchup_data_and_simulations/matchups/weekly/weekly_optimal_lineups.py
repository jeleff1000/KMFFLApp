import duckdb
import pandas as pd
import streamlit as st

def display_weekly_optimal_lineup(matchup_df: pd.DataFrame, player_df: pd.DataFrame):
    need_p = {"manager","week","year","points","optimal_player"}
    need_m = {"manager","week","year","opponent","team_points","opponent_points","win","loss","is_playoffs","is_consolation"}
    miss_p = need_p - set(player_df.columns)
    miss_m = need_m - set(matchup_df.columns)
    if miss_p:
        st.error(f"Player data missing: {sorted(miss_p)}"); return
    if miss_m:
        st.error(f"Matchup data missing: {sorted(miss_m)}"); return

    con = duckdb.connect(database=":memory:")
    con.register("p", player_df)
    con.register("m", matchup_df)

    res = con.execute("""
        WITH optimal AS (
            SELECT
                manager,
                CAST(week AS BIGINT) AS week,
                CAST(year AS BIGINT) AS year,
                SUM(CASE WHEN optimal_player = 1 THEN COALESCE(points, 0) ELSE 0 END) AS optimal_points
            FROM p
            WHERE manager IS NOT NULL
            GROUP BY manager, week, year
        ),
        joined AS (
            SELECT
                m.manager,
                CAST(m.week AS BIGINT) AS week,
                CAST(m.year AS BIGINT) AS year,
                m.opponent,
                m.team_points,
                m.opponent_points,
                CAST(m.win AS BOOLEAN) AS win,
                CAST(m.loss AS BOOLEAN) AS loss,
                CAST(m.is_playoffs AS BOOLEAN) AS is_playoffs,
                CAST(m.is_consolation AS BOOLEAN) AS is_consolation,
                COALESCE(o.optimal_points, 0) AS optimal_points
            FROM m
            LEFT JOIN optimal o
              ON o.manager = m.manager AND o.week = CAST(m.week AS BIGINT) AND o.year = CAST(m.year AS BIGINT)
            WHERE m.manager IS NOT NULL
        ),
        opp AS (
            SELECT
                j.opponent AS manager,
                j.week,
                j.year,
                j.optimal_points AS opponent_optimal
            FROM joined j
        )
        SELECT
            j.manager,
            j.week,
            j.year,
            j.opponent,
            j.team_points,
            j.optimal_points,
            j.optimal_points - j.team_points AS lost_points,
            j.win,
            j.loss,
            (j.optimal_points > COALESCE(o2.opponent_optimal, 0)) AS optimal_win,
            (j.optimal_points <= COALESCE(o2.opponent_optimal, 0)) AS optimal_loss,
            j.opponent_points,
            COALESCE(o2.opponent_optimal, 0) AS opponent_optimal,
            j.is_playoffs,
            j.is_consolation
        FROM joined j
        LEFT JOIN opp o2
          ON o2.manager = j.opponent AND o2.week = j.week AND o2.year = j.year
        ORDER BY j.year, j.week, j.manager
    """).df()
    con.close()

    # Pretty columns
    res["Year"] = res["year"].astype("Int64").astype(str)
    out = res.rename(columns={
        "week":"Week","opponent":"Opponent",
        "team_points":"Team Points","optimal_points":"Optimal Points","lost_points":"Lost Points",
        "win":"Win","loss":"Loss","optimal_win":"Optimal Win","optimal_loss":"Optimal Loss",
        "opponent_points":"Opp Pts","opponent_optimal":"Opp Optimal",
        "is_playoffs":"Is Playoffs","is_consolation":"Is Consolation",
    })[[
        "manager","Week","Year","Opponent",
        "Team Points","Optimal Points","Lost Points",
        "Win","Loss","Optimal Win","Optimal Loss",
        "Opp Pts","Opp Optimal","Is Playoffs","Is Consolation"
    ]]

    st.dataframe(out, hide_index=True)
