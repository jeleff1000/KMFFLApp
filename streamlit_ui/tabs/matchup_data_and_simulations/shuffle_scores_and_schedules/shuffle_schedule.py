import pandas as pd
import numpy as np

def shuffle_schedule(df):
    # Get unique managers and weeks
    managers = df['manager'].unique()
    weeks = df['week'].unique()

    # Create a round-robin schedule
    num_managers = len(managers)
    schedule = []

    # Shuffle managers to start at a random point
    np.random.shuffle(managers)

    # Generate round-robin matchups
    for _ in weeks:
        round_robin = []
        for i in range(num_managers // 2):
            round_robin.append((managers[i], managers[num_managers - 1 - i]))
        managers = np.roll(managers, 1)
        schedule.append(round_robin)

    # Shuffle the weeks
    np.random.shuffle(weeks)

    # Assign matchups to shuffled weeks
    final_schedule = []
    for week, matchups in zip(weeks, schedule):
        for match in matchups:
            final_schedule.append((week, match[0], match[1]))

    # Initialize Sim_Wins and Sim_Losses columns
    df['Sim_Wins'] = 0
    df['Sim_Losses'] = 0

    # Update Sim_Wins and Sim_Losses based on the new schedule
    for week, manager1, manager2 in final_schedule:
        team1_points = df[(df['manager'] == manager1) & (df['week'] == week)]['team_points'].values
        team2_points = df[(df['manager'] == manager2) & (df['week'] == week)]['team_points'].values

        if len(team1_points) > 0 and len(team2_points) > 0:
            if team1_points[0] > team2_points[0]:
                df.loc[(df['manager'] == manager1) & (df['week'] == week), 'Sim_Wins'] += 1
                df.loc[(df['manager'] == manager2) & (df['week'] == week), 'Sim_Losses'] += 1
            elif team1_points[0] < team2_points[0]:
                df.loc[(df['manager'] == manager1) & (df['week'] == week), 'Sim_Losses'] += 1
                df.loc[(df['manager'] == manager2) & (df['week'] == week), 'Sim_Wins'] += 1

    return df