import pandas as pd
import numpy as np
import duckdb

def duckdb_filter(df, sql):
    con = duckdb.connect()
    con.register('df', df)
    result = con.execute(sql).fetchdf()
    con.close()
    return result

def calculate_std_dev(df, selected_year, show_regular_season, show_postseason):
    # Build DuckDB WHERE clause
    where = []
    if selected_year != "All Years":
        where.append(f"year = '{selected_year}'")
    if not show_regular_season:
        where.append("is_playoffs = TRUE")
    if not show_postseason:
        where.append("is_playoffs = FALSE")
    where_clause = " AND ".join(where)
    sql = f"""
        SELECT manager, stddev_samp(team_points) AS StdDev_TeamPoints
        FROM df
        {f'WHERE {where_clause}' if where_clause else ''}
        GROUP BY manager
    """
    return duckdb_filter(df, sql)

def tweak_scores(df, std_dev_df):
    df = df.merge(std_dev_df, on='manager', how='left')
    df['tweaked_team_points'] = df.apply(
        lambda row: row['team_points'] + np.random.uniform(-1/3, 1/3) * row['StdDev_TeamPoints'], axis=1
    )
    df['Sim_Wins'] = 0
    df['Sim_Losses'] = 0
    for index, row in df.iterrows():
        opponent_week = df[(df['manager'] == row['opponent']) & (df['week'] == row['week'])]
        if not opponent_week.empty:
            opponent_points = opponent_week.iloc[0]['team_points']
            if row['tweaked_team_points'] > opponent_points:
                df.at[index, 'Sim_Wins'] = 1
            elif row['tweaked_team_points'] < opponent_points:
                df.at[index, 'Sim_Losses'] = 1
    return df

def calculate_playoff_seed(df):
    # Use DuckDB for aggregation and sorting
    con = duckdb.connect()
    con.register('df', df)
    agg_df = con.execute("""
        SELECT manager,
               SUM(Sim_Wins) AS Sim_Wins,
               SUM(tweaked_team_points) AS Total_Tweaked_Points
        FROM df
        GROUP BY manager
        ORDER BY Sim_Wins DESC, Total_Tweaked_Points DESC
    """).fetchdf()
    agg_df['Sim_Playoff_Seed'] = range(1, len(agg_df) + 1)
    con.close()
    df = df.merge(agg_df[['manager', 'Sim_Playoff_Seed']], on='manager', how='left')
    return df

def main(df, selected_year, show_regular_season, show_postseason, tweak_scores_flag):
    std_dev_df = calculate_std_dev(df, selected_year, show_regular_season, show_postseason)
    if tweak_scores_flag:
        df = tweak_scores(df, std_dev_df)
    df = calculate_playoff_seed(df)
    return df