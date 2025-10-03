import streamlit as st
import pandas as pd
import duckdb
import re
from .matchups.weekly.weekly_matchup_overview import WeeklyMatchupDataViewer

def duckdb_filter(df, sql):
    con = duckdb.connect()
    con.register('df', df)
    result = con.execute(sql).fetchdf()
    con.close()
    return result

class EveryonesScheduleViewer(WeeklyMatchupDataViewer):
    def __init__(self, matchup_data_df, player_data_df):
        super().__init__(matchup_data_df, player_data_df)
        self.df = matchup_data_df

    def display(self):
        st.subheader("Everyone's Schedule Simulation")

        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        with col1:
            years = ["All"] + sorted(self.df['year'].astype(int).unique().tolist())
            default_year = max(years[1:])
            selected_year = st.selectbox("Select Year", years, index=years.index(default_year), key="everyones_schedule_year_dropdown")

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

        # Extract opponent names from columns
        win_cols = [c for c in filtered_df.columns if re.match(r"w_vs_(.+)_sched", c)]
        opponent_names = [re.match(r"w_vs_(.+)_sched", c).group(1) for c in win_cols]

        # Filter out opponents where both win and loss columns sum to zero
        valid_opponents = []
        for opponent in opponent_names:
            w_col = f"w_vs_{opponent}_sched"
            l_col = f"l_vs_{opponent}_sched"
            if w_col in filtered_df.columns and l_col in filtered_df.columns:
                if filtered_df[w_col].sum() + filtered_df[l_col].sum() > 0:
                    valid_opponents.append(opponent)

        result_df = pd.DataFrame(columns=['manager'] + [f"{opponent.title()}'s" for opponent in valid_opponents])
        result_df['manager'] = filtered_df['manager'].unique()

        for manager in result_df['manager']:
            manager_rows = filtered_df[filtered_df['manager'] == manager]
            for opponent in valid_opponents:
                w_col = f"w_vs_{opponent}_sched"
                l_col = f"l_vs_{opponent}_sched"
                wins = manager_rows[w_col].sum() if w_col in manager_rows else 0
                losses = manager_rows[l_col].sum() if l_col in manager_rows else 0
                result_df.loc[result_df['manager'] == manager, f"{opponent.title()}'s"] = f"{int(wins)}-{int(losses)}"

        result_df = result_df.sort_values(by='manager').reset_index(drop=True)

        def highlight_matching_cells(val, manager, column):
            color = 'yellow' if manager.lower() in column.lower() else ''
            font_weight = 'bold' if manager.lower() in column.lower() else 'normal'
            return f'background-color: {color}; font-weight: {font_weight}'

        styled_df = result_df.style.apply(
            lambda x: [highlight_matching_cells(v, x['manager'], col) for col, v in x.items()], axis=1
        )
        st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)