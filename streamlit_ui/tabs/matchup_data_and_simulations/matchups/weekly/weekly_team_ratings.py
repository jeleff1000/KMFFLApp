from __future__ import annotations
from typing import Dict, List
import pandas as pd
import streamlit as st

class WeeklyTeamRatingsViewer:
    """
    Streamlined Streamlit viewer for weekly team ratings.
    Assumes filtering is handled by the parent view.
    Shows only the original columns, reordered with the requested fields first.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        # Drop duplicate-named columns, keep first occurrence
        self.base_df = df.loc[:, ~df.columns.duplicated()].copy()

        # Known numeric columns for coercion/formatting
        self.numeric_cols: List[str] = [
            "team_points", "win", "loss", "opponent_points",
            "avg_seed", "p_playoffs", "p_bye", "exp_final_wins",
            "p_semis", "p_final", "p_champ",
            "x1_seed", "shuffle_1_seed", "shuffle_avg_wins",
            "wins_vs_shuffle_wins", "shuffle_avg_playoffs",
            "shuffle_avg_bye", "shuffle_avg_seed",
            "seed_vs_shuffle_seed", "power_rating", "power rating",
        ]
        for c in self.numeric_cols:
            if c in self.base_df.columns:
                self.base_df[c] = pd.to_numeric(self.base_df[c], errors="coerce")

        # Ensure 'year' and 'week' types if present
        for c in ["year", "week", "OpponentYear", "Opponent Week"]:
            if c in self.base_df.columns:
                self.base_df[c] = pd.to_numeric(self.base_df[c], errors="ignore")

        # Columns to hide from display
        self.hidden_cols: List[str] = ["Opponent Week", "OpponentYear"]

        # Leading order: manager first
        self.leading_order: List[str] = [
            "manager", "week", "year", "team_points", "power_rating", "power rating",
        ]

        # Remaining original columns (excluding hidden ones)
        self.secondary_order: List[str] = [
            "Winning Streak", "Losing Streak",
            "avg_seed", "x1_seed",
            "p_playoffs", "p_bye", "exp_final_wins", "p_semis", "p_final", "p_champ",
            "shuffle_1_seed", "shuffle_avg_wins", "wins_vs_shuffle_wins",
            "shuffle_avg_playoffs", "shuffle_avg_bye", "shuffle_avg_seed",
            "seed_vs_shuffle_seed",
        ]

    def _present(self, cols: List[str]) -> List[str]:
        return [c for c in cols if c in self.base_df.columns]

    def _prob_cols(self) -> List[str]:
        return [c for c in ["p_playoffs", "p_bye", "p_semis", "p_final", "p_champ"] if c in self.base_df.columns]

    def display(self, prefix: str = "weekly_team_ratings") -> None:
        st.subheader("Weekly Team Ratings")

        if self.base_df.empty:
            st.info("No data available.")
            return

        # Internal sort: power_rating -> power rating -> team_points
        sort_candidates = ["power_rating", "power rating", "team_points"]
        sort_col = next((c for c in sort_candidates if c in self.base_df.columns), None)

        df = self.base_df.copy()
        if sort_col:
            df = df.sort_values(by=sort_col, ascending=False)

        # Only original columns: leading first, then the rest; do not append any other columns
        leading = self._present(self.leading_order)
        secondary = [c for c in self._present(self.secondary_order) if c not in leading]
        show_cols = [c for c in (leading + secondary) if c not in self.hidden_cols]

        if not show_cols:
            st.warning("No known columns to display.")
            return

        df_show = df[show_cols].copy()

        # Format probability columns as percents
        prob_cols = [c for c in self._prob_cols() if c in df_show.columns]
        column_config: Dict[str, st.column_config.Column] = {}
        for c in prob_cols:
            column_config[c] = st.column_config.NumberColumn(c, format="%.1f%%")
            if df_show[c].dropna().between(0, 1).all():
                df_show[c] = df_show[c] * 100.0

        # Numeric formatting
        for c in ["team_points", "power_rating", "power rating", "exp_final_wins", "avg_seed", "x1_seed",
                  "shuffle_avg_wins", "shuffle_avg_playoffs", "shuffle_avg_bye", "shuffle_avg_seed"]:
            if c in df_show.columns:
                column_config[c] = st.column_config.NumberColumn(c, format="%.2f")
        for c in ["win", "loss", "wins_vs_shuffle_wins", "shuffle_1_seed", "seed_vs_shuffle_seed",
                  "opponent_points", "week", "year"]:
            if c in df_show.columns:
                column_config[c] = st.column_config.NumberColumn(c, format="%d")

        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            column_config=column_config or None,
        )