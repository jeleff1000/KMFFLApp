# weekly_player_advanced_stats.py

import pandas as pd

def get_advanced_stats(player_data, position):
    if position == 'QB':
        columns = [
            'player', 'team', 'week', 'season', 'owner', 'points', 'position',
            'Pass Yds', 'completions', 'attempts', 'Int Pass TD', 'sack_yards',
            'sack_fumbles', 'passing_2pt_conversions', 'passing_air_yards',
            'passing_yards_after_catch', 'passing_first_downs', 'passing_epa',
            'dakota', 'pacr', 'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles',
            'rushing_fumbles_lost', 'rushing_first_downs', 'rushing_epa'
        ]
        return player_data[columns]
    else:
        return player_data[['player']]  # Default case for other positions