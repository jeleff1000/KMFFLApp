import streamlit as st
import numpy as np
import pandas as pd

class PlayoffOddsViewer:
    def __init__(self, matchup_data_df):
        self.df = matchup_data_df.copy()

    def display(self):
        st.subheader("Playoff Odds Monte Carlo Simulation")
        df = self.df[(self.df["is_consolation"] == 0)].copy()
        seasons = sorted(df["year"].unique())
        max_season = max(seasons)

        sim_mode = st.radio("Simulation Start", ["Start from Today", "Start from Specific Date"])
        if sim_mode == "Start from Today":
            season = max_season
            all_weeks = sorted(df[df["year"] == season]["week"].unique())
            week = max(all_weeks)
            go_clicked = st.button("Go", key="go_today")
        else:
            cols = st.columns([2, 2, 1])
            season = cols[0].selectbox("Select Season", seasons, index=len(seasons) - 1)
            all_weeks = sorted(df[df["year"] == season]["week"].unique())
            week = cols[1].selectbox("Select Week", all_weeks, index=len(all_weeks) - 1)
            go_clicked = cols[2].button("Go", key="go_specific")

        reg_season_raw = df[(df["year"] == season) & (df["is_playoffs"] == 0)].copy()
        odds = reg_season_raw[reg_season_raw["week"] == week].copy()

        odds_cols = [
            "avg_seed", "Manager", "p_playoffs", "p_bye", "exp_final_wins",
            "exp_final_pf", "p_semis", "p_final", "p_champ"
        ]
        odds_table = odds[odds_cols].sort_values("avg_seed", ascending=True).reset_index(drop=True)

        n_teams = reg_season_raw["Manager"].nunique()
        seed_cols = [f"x{i}_seed" for i in range(1, n_teams + 1)]
        # Set Manager as index, sort, and set index name
        seed_dist = odds[["Manager"] + seed_cols].set_index("Manager").sort_index()
        seed_dist.index.name = None  # Remove the index label

        if go_clicked:
            st.subheader("Simulation Odds")
            st.dataframe(odds_table, hide_index=True)
            st.subheader("Seed Distribution")
            styled = seed_dist.style.background_gradient(
                subset=seed_cols, cmap="RdYlGn"
            ).format("{:.2f}", subset=seed_cols)
            st.markdown(styled.to_html(escape=False, index=True), unsafe_allow_html=True)