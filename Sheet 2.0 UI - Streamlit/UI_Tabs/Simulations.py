import numpy as np
import pandas as pd
import random
from itertools import permutations
import streamlit as st
from UI_Tabs.Simulations.Odds_of_Every_Record import calculate_odds_of_every_record
from UI_Tabs.Simulations.Gavi_Stat import calculate_gavi_stat  # Ensure this import is correct

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

def display_simulations_viewer(df):
    st.header("Simulations Viewer")
    years = df['year'].astype(str).unique().tolist()
    years.insert(0, "All Years")

    simulation_type = st.selectbox("Select Simulation Type", ["Gavi Stat", "Opponent Gavi Stat", "Odds of Every Record"])
    selected_year = st.selectbox("Select Year", years)
    include_playoffs = st.checkbox("Include Playoffs", value=True, key="include_playoffs_simulation")
    include_regular_season = st.checkbox("Include Regular Season", value=True, key="include_regular_season_simulation")

    if st.button("Calculate Simulation"):
        if simulation_type == "Gavi Stat":
            gavi_stat_df = calculate_gavi_stat(df, selected_year, include_playoffs)
        elif simulation_type == "Opponent Gavi Stat":
            gavi_stat_df = calculate_gavi_stat(df, selected_year, include_playoffs, opponent=True)
        elif simulation_type == "Odds of Every Record":
            gavi_stat_df = calculate_odds_of_every_record(df)

        st.write("Simulation Results")
        st.dataframe(gavi_stat_df)