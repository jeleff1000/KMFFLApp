# Opponent Gavi Stat.py
import pandas as pd

def calculate_opponent_gavi_stat(df, selected_year, include_playoffs):
    if selected_year != "All Years":
        df = df[df['year'] == int(selected_year)]

    df = df[df['is_consolation'] != 1]
    if not include_playoffs:
        df = df[df['is_playoffs'] != 1]

    df['teams_beat_this_week'] = df['teams_beat_this_week'].fillna(0)

    gavi_stat_df = df.groupby('opponent').agg(
        win=('win', 'sum'),
        loss=('win', 'count'),
        teams_beat_this_week=('teams_beat_this_week', 'sum')
    ).reset_index()
    gavi_stat_df.rename(columns={'opponent': 'Manager'}, inplace=True)
    gavi_stat_df['loss'] = gavi_stat_df['loss'] - gavi_stat_df['win']
    gavi_stat_df['record'] = gavi_stat_df['loss'].astype(str) + " - " + gavi_stat_df['win'].astype(str)
    gavi_stat_df['expected_wins'] = (gavi_stat_df['teams_beat_this_week'] / 9).round(2)
    gavi_stat_df['expected_record'] = (gavi_stat_df['win'] + gavi_stat_df['loss'] - gavi_stat_df['expected_wins']).round(2).astype(str) + " - " + gavi_stat_df['expected_wins'].round(2).astype(str)
    gavi_stat_df['delta'] = (gavi_stat_df['expected_wins'] - gavi_stat_df['win']).round(2)

    return gavi_stat_df