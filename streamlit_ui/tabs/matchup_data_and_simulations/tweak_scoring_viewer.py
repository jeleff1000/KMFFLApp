import streamlit as st
import duckdb
import numpy as np
from .matchups.weekly.weekly_matchup_overview import WeeklyMatchupDataViewer
from .shuffle_scores_and_schedules.shuffle_scores import calculate_std_dev, tweak_scores, calculate_playoff_seed
from .shuffle_scores_and_schedules.shuffle_schedule import shuffle_schedule

def duckdb_filter(df, sql):
    con = duckdb.connect()
    con.register('df', df)
    result = con.execute(sql).fetchdf()
    con.close()
    return result

class TweakScoringViewer(WeeklyMatchupDataViewer):
    def __init__(self, matchup_data_df, player_data_df):
        super().__init__(matchup_data_df, player_data_df)
        self.df = matchup_data_df

    def display(self):
        if self.df is not None:
            col1, col2 = st.columns([1, 3])
            with col1:
                years = ["All Years"] + sorted(self.df['year'].unique().tolist())
                default_year = max(self.df['year'].unique().tolist())
                selected_year = st.selectbox("Select Year", years, index=years.index(default_year))

            col3, col4 = st.columns([1, 1])
            with col3:
                show_regular_season = st.checkbox("Regular Season", value=True, key="regular_season_checkbox")
            with col4:
                show_postseason = st.checkbox("Postseason", value=False, key="postseason_checkbox")

            col5, col6 = st.columns([1, 1])
            with col5:
                tweak_scores_flag = st.checkbox("Tweak Scores", key="tweak_scores_checkbox")
            with col6:
                shuffle_schedule_flag = st.checkbox("Shuffle Schedule", key="shuffle_schedule_checkbox")

            if st.button("Simulate"):
                # DuckDB filtering
                where = []
                if selected_year != "All Years":
                    where.append(f"year = '{selected_year}'")
                if show_regular_season and show_postseason:
                    where.append("((is_playoffs = 0 AND is_consolation = 0) OR is_playoffs = 1)")
                elif show_regular_season:
                    where.append("(is_playoffs = 0 AND is_consolation = 0)")
                elif show_postseason:
                    where.append("is_playoffs = 1")
                where_clause = " AND ".join(where)
                sql = f"SELECT * FROM df" + (f" WHERE {where_clause}" if where_clause else "")
                filtered_df = duckdb_filter(self.df, sql)

                if shuffle_schedule_flag:
                    filtered_df = shuffle_schedule(filtered_df)

                if 'tweaked_team_points' not in filtered_df.columns:
                    filtered_df['tweaked_team_points'] = filtered_df['team_points']

                if tweak_scores_flag:
                    std_dev_df = calculate_std_dev(filtered_df, selected_year, show_regular_season, show_postseason)
                    filtered_df = tweak_scores(filtered_df, std_dev_df)

                if 'Sim_Wins' not in filtered_df.columns:
                    filtered_df['Sim_Wins'] = 0
                if 'Sim_Losses' not in filtered_df.columns:
                    filtered_df['Sim_Losses'] = 0

                filtered_df = calculate_playoff_seed(filtered_df)

                if 'Sim_Playoff_Seed' not in filtered_df.columns:
                    filtered_df['Sim_Playoff_Seed'] = np.nan

                # DuckDB aggregation for playoff_seed_to_date at largest week
                con = duckdb.connect()
                con.register('filtered_df', filtered_df)
                agg_sql = """
                    WITH latest_week AS (
                        SELECT 
                            year, manager, MAX(week) AS max_week
                        FROM filtered_df
                        GROUP BY year, manager
                    ),
                    seeds AS (
                        SELECT 
                            f.year, f.manager, f.playoff_seed_to_date
                        FROM filtered_df f
                        INNER JOIN latest_week lw
                        ON f.year = lw.year AND f.manager = lw.manager AND f.week = lw.max_week
                    )
                    SELECT 
                        f.year,
                        f.manager,
                        SUM(f.team_points) AS Points,
                        SUM(f.tweaked_team_points) AS Sim_Points,
                        SUM(f.Sim_Wins) AS Sim_W,
                        SUM(f.Sim_Losses) AS Sim_L,
                        SUM(f.win) AS Wins,
                        SUM(f.loss) AS Losses,
                        s.playoff_seed_to_date AS Seed,
                        MAX(f.Sim_Playoff_Seed) AS Sim_Seed
                    FROM filtered_df f
                    LEFT JOIN seeds s
                    ON f.year = s.year AND f.manager = s.manager
                    GROUP BY f.year, f.manager, s.playoff_seed_to_date
                """
                aggregated_df = con.execute(agg_sql).fetchdf()
                con.close()

                aggregated_df['year'] = aggregated_df['year'].astype(str)
                aggregated_df = aggregated_df.sort_values(by=['Seed'])

                data_columns = ['manager', 'Seed', 'Wins', 'Losses', 'Points']
                sim_columns = ['manager', 'Sim_Seed', 'Sim_W', 'Sim_L', 'Sim_Points']

                if selected_year == "All Years":
                    data_columns.insert(0, 'year')
                    sim_columns.insert(0, 'year')

                sim_aggregated_df = aggregated_df.sort_values(by=['Sim_Seed'])

                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(aggregated_df[data_columns], hide_index=True)
                with col2:
                    st.dataframe(sim_aggregated_df[sim_columns], hide_index=True)