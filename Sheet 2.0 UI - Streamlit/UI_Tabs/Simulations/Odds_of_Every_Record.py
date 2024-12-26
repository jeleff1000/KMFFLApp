# File: Simulations/odds_of_every_record.py

import numpy as np
import pandas as pd
from itertools import permutations

def calculate_wins(scores):
    wins = []
    for score in scores:
        win_count = sum(score > other_score for other_score in scores)
        wins.append(win_count)
    return wins

def calculate_probabilities(num_weeks, wins_per_week):
    total_records = num_weeks + 1
    win_probs = [0] * total_records
    win_probs[0] = 1.0

    for week in range(num_weeks):
        new_probs = [0] * total_records
        for wins in range(total_records):
            if wins > 0:
                new_probs[wins] += win_probs[wins - 1] * (wins_per_week[week] / 9)
            new_probs[wins] += win_probs[wins] * (1 - (wins_per_week[week] / 9))
        win_probs = new_probs

    return win_probs[::-1]

def generate_all_schedules(num_teams, num_weeks):
    teams = list(range(num_teams))
    all_schedules = []

    for perm in permutations(teams):
        schedule = []
        for week in range(num_weeks):
            week_matches = []
            for i in range(0, num_teams, 2):
                week_matches.append((perm[i], perm[i+1]))
            schedule.append(week_matches)
        all_schedules.append(schedule)

    return all_schedules

def enforce_schedule_rules(schedule, num_teams, num_weeks):
    match_count = {team: {opponent: 0 for opponent in range(num_teams)} for team in range(num_teams)}

    for week in schedule:
        for team1, team2 in week:
            match_count[team1][team2] += 1
            match_count[team2][team1] += 1

    for week in schedule:
        for team1, team2 in week:
            if match_count[team1][team2] > 2 or match_count[team2][team1] > 2:
                return False
            if num_weeks >= 12:
                for team in range(num_teams):
                    opponents = [opponent for opponent in range(num_teams) if match_count[team][opponent] > 0]
                    if len(opponents) != num_teams - 1:
                        return False
    return True

def calculate_odds_of_every_record(df):
    num_teams = len(df.index)
    num_weeks = df.shape[1]
    all_schedules = generate_all_schedules(num_teams, num_weeks)
    valid_schedules = [schedule for schedule in all_schedules if enforce_schedule_rules(schedule, num_teams, num_weeks)]

    team_names = df.index
    team_results = []

    for schedule in valid_schedules:
        weekly_results = []
        for week in range(num_weeks):
            scores_this_week = df.iloc[:, week].values
            wins_this_week = calculate_wins(scores_this_week)
            weekly_results.append(wins_this_week)
        team_results.append(weekly_results)

    final_probabilities = []
    for week_wins in zip(*team_results):
        probabilities = calculate_probabilities(num_weeks, week_wins)
        final_probabilities.append(probabilities)

    record_columns = [f"{wins}-{num_weeks - wins}" for wins in range(num_weeks, -1, -1)]
    result_df = pd.DataFrame(final_probabilities, index=team_names, columns=record_columns)

    result_df = result_df * 100

    for col in record_columns:
        result_df[col] = result_df[col].apply(lambda x: f"{x:.2f}%")

    average_wins_losses = []
    for team in team_names:
        avg_wins = sum((wins * (float(prob.replace('%', '')) / 100) for wins, prob in zip(range(num_weeks, -1, -1), result_df.loc[team])))
        avg_losses = num_weeks - avg_wins
        average_wins_losses.append(f"{avg_wins:.2f}-{avg_losses:.2f}")

    result_df['Average Wins-Losses'] = average_wins_losses

    return result_df