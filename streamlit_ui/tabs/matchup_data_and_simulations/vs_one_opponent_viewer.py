import streamlit as st
import pandas as pd
import duckdb
import re

def duckdb_filter(df, sql):
    con = duckdb.connect()
    con.register('df', df)
    result = con.execute(sql).fetchdf()
    con.close()
    return result

class VsOneOpponentViewer:
    def __init__(self, df):
        self.df = df

    def display(self):
        st.subheader("Vs. One Opponent Simulation")

        # Year and season filters
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        with col1:
            years = ["All"] + sorted(self.df['year'].astype(int).unique())
            default_year = max(years[1:])
            selected_year = st.selectbox("Select Year", years, index=years.index(default_year), key="vs_one_opponent_year_dropdown")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            include_regular_season = st.checkbox("Include Regular Season", value=True, key="include_regular_season")
        with col2:
            include_postseason = st.checkbox("Include Postseason", value=False, key="include_postseason")

        # DuckDB filtering
        year_clause = "" if selected_year == "All" else f"year={int(selected_year)}"
        season_clauses = []
        if include_regular_season:
            season_clauses.append("(is_playoffs=0 AND is_consolation=0)")
        if include_postseason:
            season_clauses.append("(is_playoffs=1 OR is_consolation=1)")
        where_clauses = " AND ".join(filter(None, [year_clause]))
        if season_clauses:
            where_clauses += (" AND " if where_clauses else "") + "(" + " OR ".join(season_clauses) + ")"
        sql = f"SELECT * FROM df" + (f" WHERE {where_clauses}" if where_clauses else "")
        filtered_df = duckdb_filter(self.df, sql)

        # Find all opponent suffixes (no _sched)
        win_cols = [c for c in filtered_df.columns if c.startswith("w_vs_") and not c.endswith("_sched")]
        loss_cols = [c for c in filtered_df.columns if c.startswith("l_vs_") and not c.endswith("_sched")]
        suffixes = set([c[5:] for c in win_cols]) & set([c[5:] for c in loss_cols])

        # Only keep suffixes where sum of both columns > 0
        valid_opponents = []
        for suffix in suffixes:
            w_col = f"w_vs_{suffix}"
            l_col = f"l_vs_{suffix}"
            if w_col in filtered_df.columns and l_col in filtered_df.columns:
                if filtered_df[w_col].sum() + filtered_df[l_col].sum() > 0:
                    valid_opponents.append(suffix)

        valid_opponents = sorted(valid_opponents)  # <-- Sort alphabetically

        managers = filtered_df['manager'].unique().tolist()
        result_df = pd.DataFrame(columns=['manager'] + [f"{opponent.title()}" for opponent in valid_opponents])
        result_df['manager'] = managers

        for manager in managers:
            manager_rows = filtered_df[filtered_df['manager'] == manager]
            for opponent in valid_opponents:
                w_col = f"w_vs_{opponent}"
                l_col = f"l_vs_{opponent}"
                wins = manager_rows[w_col].sum() if w_col in manager_rows else 0
                losses = manager_rows[l_col].sum() if l_col in manager_rows else 0
                result_df.loc[result_df['manager'] == manager, f"{opponent.title()}"] = f"{int(wins)}-{int(losses)}"

        result_df = result_df.sort_values(by='manager').reset_index(drop=True)

        def highlight_diagonal(val, manager, column):
            if manager.lower() in column.lower():
                return 'background-color: yellow; font-weight: bold'
            return ''

        styled_df = result_df.style.apply(
            lambda x: [highlight_diagonal(v, x['manager'], col) for col, v in x.items()], axis=1
        )
        st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)