import streamlit as st
import duckdb
import pandas as pd

class KeeperDataViewer:
    def __init__(self, keeper_data):
        self.keeper_data = keeper_data

    def display(self):
        df = self.keeper_data.copy()
        df['year'] = df['year'].astype(str)
        df['manager'] = df['manager'].astype(str)
        df = df.rename(columns={
            'Is Keeper Status': 'is_keeper_status',
            'team': 'nfl_team'
        })

        con = duckdb.connect()
        con.register('keepers', df)

        # Filter to only the largest week in each manager/year
        query = """
            SELECT *
            FROM keepers
            WHERE manager != 'No manager'
              AND yahoo_position NOT IN ('DEF', 'K')
              AND week = (
                  SELECT max(week)
                  FROM keepers k2
                  WHERE k2.manager = keepers.manager AND k2.year = keepers.year
              )
        """
        df_filtered = con.execute(query).df()

        managers = ["All"] + sorted(df_filtered['manager'].unique().tolist())
        years = ["All"] + sorted(df_filtered['year'].unique().tolist())

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            selected_managers = st.multiselect("Select manager(s)", managers, default=[], key="keepers_manager_multiselect")
        with col2:
            selected_years = st.multiselect("Select Year(s)", years, default=[], key="keepers_year_multiselect")
        with col3:
            st.write("")
            go_button = st.button("Go", key="keepers_go_button")

        if go_button:
            where_clauses = []
            if selected_managers and "All" not in selected_managers:
                managers_str = ",".join([f"'{m}'" for m in selected_managers])
                where_clauses.append(f"manager IN ({managers_str})")
            if selected_years and "All" not in selected_years:
                years_str = ",".join([f"'{y}'" for y in selected_years])
                where_clauses.append(f"year IN ({years_str})")
            where_sql = " AND ".join(where_clauses)
            if where_sql:
                query = f"SELECT * FROM df_filtered WHERE {where_sql}"
                result_df = con.execute(query).df()
            else:
                result_df = df_filtered

            columns_to_display = [
                'player', 'kept_next_year', 'is_keeper_status', 'keeper_price', 'nfl_team', 'manager', 'yahoo_position', 'year',
                'avg_points_this_year', 'avg_points_next_year', 'avg_cost_next_year',
                'cost', 'faab_bid', 'total_points_next_year'
            ]
            result_df = result_df[columns_to_display]
            result_df = result_df.dropna(how='all', subset=columns_to_display)

            result_df['kept_next_year'] = result_df['kept_next_year'].astype(bool)
            result_df['is_keeper_status'] = result_df['is_keeper_status'].astype(bool)

            st.dataframe(result_df, height=600, width=1200, hide_index=True)