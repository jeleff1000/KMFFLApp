import pandas as pd
import numpy as np
import duckdb

def duckdb_filter(df, sql):
    con = duckdb.connect()
    con.register('df', df)
    result = con.execute(sql).fetchdf()
    con.close()
    return result

def shuffle_schedule(df):
    # Get unique managers and weeks using DuckDB
    managers = duckdb_filter(df, "SELECT DISTINCT manager FROM df")['manager'].values
    weeks = duckdb_filter(df, "SELECT DISTINCT week FROM df")['week'].values

    num_managers = len(managers)
    schedule = []

    np.random.shuffle(managers)

    for _ in weeks:
        round_robin = []
        for i in range(num_managers // 2):
            round_robin.append((managers[i], managers[num_managers - 1 - i]))
        managers = np.roll(managers, 1)
        schedule.append(round_robin)

    np.random.shuffle(weeks)

    final_schedule = []
    for week, matchups in zip(weeks, schedule):
        for match in matchups:
            final_schedule.append((week, match[0], match[1]))

    df['Sim_Wins'] = 0
    df['Sim_Losses'] = 0

    con = duckdb.connect()
    con.register('df', df)

    for week, manager1, manager2 in final_schedule:
        # Get team points for both managers for the week using DuckDB
        sql1 = f"SELECT team_points FROM df WHERE manager='{manager1}' AND week={week}"
        sql2 = f"SELECT team_points FROM df WHERE manager='{manager2}' AND week={week}"
        team1_points = con.execute(sql1).fetchdf()['team_points'].values
        team2_points = con.execute(sql2).fetchdf()['team_points'].values

        if len(team1_points) > 0 and len(team2_points) > 0:
            if team1_points[0] > team2_points[0]:
                df.loc[(df['manager'] == manager1) & (df['week'] == week), 'Sim_Wins'] += 1
                df.loc[(df['manager'] == manager2) & (df['week'] == week), 'Sim_Losses'] += 1
            elif team1_points[0] < team2_points[0]:
                df.loc[(df['manager'] == manager1) & (df['week'] == week), 'Sim_Losses'] += 1
                df.loc[(df['manager'] == manager2) & (df['week'] == week), 'Sim_Wins'] += 1

    con.close()
    return df