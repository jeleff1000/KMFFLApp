import streamlit as st
import duckdb

class PlayoffOddsViewer:
    def __init__(self, matchup_data_df):
        self.df = matchup_data_df.copy()

    def duckdb_query(self, sql):
        con = duckdb.connect()
        con.register('df', self.df)
        result = con.execute(sql).fetchdf()
        con.close()
        return result

    def display(self):
        st.subheader("Playoff Odds Monte Carlo Simulation")
        # Filter out consolation using DuckDB
        sql = "SELECT * FROM df WHERE is_consolation = 0"
        df = self.duckdb_query(sql)
        seasons = sorted(df["year"].unique())
        max_season = max(seasons)

        sim_mode = st.radio("Simulation Start", ["Start from Today", "Start from Specific Date"])
        if sim_mode == "Start from Today":
            season = max_season
            sql_weeks = f"SELECT DISTINCT week FROM df WHERE year = {season}"
            all_weeks = sorted(self.duckdb_query(sql_weeks)["week"].tolist())
            week = max(all_weeks)
            go_clicked = st.button("Go", key="go_today")
        else:
            cols = st.columns([2, 2, 1])
            season = cols[0].selectbox("Select Season", seasons, index=len(seasons) - 1)
            sql_weeks = f"SELECT DISTINCT week FROM df WHERE year = {season}"
            all_weeks = sorted(self.duckdb_query(sql_weeks)["week"].tolist())
            week = cols[1].selectbox("Select Week", all_weeks, index=len(all_weeks) - 1)
            go_clicked = cols[2].button("Go", key="go_specific")

        # Filter regular season and week using DuckDB
        sql_odds = f"""
            SELECT *
            FROM df
            WHERE year = {season}
              AND is_playoffs = 0
              AND week = {week}
        """
        odds = self.duckdb_query(sql_odds)

        odds_cols = [
            "avg_seed", "manager", "p_playoffs", "p_bye", "exp_final_wins",
            "exp_final_pf", "p_semis", "p_final", "p_champ"
        ]
        odds_table = odds[odds_cols].sort_values("avg_seed", ascending=True).reset_index(drop=True)

        if go_clicked:
            st.subheader("Simulation Odds")
            st.dataframe(odds_table, hide_index=True)