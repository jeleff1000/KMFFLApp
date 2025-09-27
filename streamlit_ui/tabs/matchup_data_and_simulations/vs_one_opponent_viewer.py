import streamlit as st
import pandas as pd
import re

class VsOneOpponentViewer:
    def __init__(self, df):
        self.df = df

    def display(self):
        st.subheader("Vs. One Opponent Simulation")

        # Year and season filters
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        with col1:
            years = ["All"] + sorted(self.df['year'].astype(int).unique().tolist())
            default_year = max(years[1:])
            selected_year = st.selectbox("Select Year", years, index=years.index(default_year), key="vs_one_opponent_year_dropdown")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            include_regular_season = st.checkbox("Include Regular Season", value=True, key="include_regular_season")
        with col2:
            include_postseason = st.checkbox("Include Postseason", value=False, key="include_postseason")

        # Filter data
        if selected_year != "All":
            filtered_df = self.df[self.df['year'] == int(selected_year)]
        else:
            filtered_df = self.df

        if include_regular_season:
            regular_season_df = filtered_df[(filtered_df['is_playoffs'] == 0) & (filtered_df['is_consolation'] == 0)]
        else:
            regular_season_df = pd.DataFrame()

        if include_postseason:
            postseason_df = filtered_df[(filtered_df['is_playoffs'] == 1) | (filtered_df['is_consolation'] == 1)]
        else:
            postseason_df = pd.DataFrame()

        filtered_df = pd.concat([regular_season_df, postseason_df])

        # Dynamically find all opponent suffixes, excluding *_SCHED (case-insensitive)
        win_cols = [col for col in filtered_df.columns if re.match(r'w_vs_', col, re.IGNORECASE)]
        suffixes = [col[5:] for col in win_cols]
        suffixes = [
            s for s in suffixes
            if f'l_vs_{s}' in filtered_df.columns and not s.lower().endswith('_sched')
        ]

        # Group by manager and sum
        result_df = filtered_df.groupby('manager').sum(numeric_only=True).reset_index()

        # Combine win/loss columns for each opponent
        for suffix in suffixes:
            win_col = f'w_vs_{suffix}'
            loss_col = f'l_vs_{suffix}'
            display_col = f"Vs {suffix.title()}"
            result_df[display_col] = result_df[win_col].astype(int).astype(str) + "-" + result_df[loss_col].astype(int).astype(str)
            result_df = result_df.drop(columns=[win_col, loss_col])

        # Keep only manager and combined columns
        display_cols = ['manager'] + [f"Vs {s.title()}" for s in suffixes]
        result_df = result_df[display_cols]

        st.markdown(result_df.to_html(index=False, escape=False), unsafe_allow_html=True)

        # Win-loss table
        win_loss_df = filtered_df.groupby('manager').agg({'win': 'sum', 'loss': 'sum'}).reset_index()
        win_loss_df['Win-Loss'] = win_loss_df['win'].astype(int).astype(str) + "-" + win_loss_df['loss'].astype(int).astype(str)
        win_loss_df = win_loss_df.set_index('manager')
        st.subheader("Win-Loss Record for Each manager")
        st.dataframe(win_loss_df[['Win-Loss']])