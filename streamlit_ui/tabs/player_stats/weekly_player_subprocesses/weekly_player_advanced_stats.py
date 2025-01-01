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
    elif position == 'RB':
        columns = [
            'player', 'team', 'week', 'season', 'owner', 'points', 'position',
            'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles', 'rushing_fumbles_lost',
            'rushing_first_downs', 'rushing_epa', 'targets', 'receptions', 'Rec Yds',
            'Rec TD', 'receiving_fumbles', 'receiving_fumbles_lost', 'receiving_first_downs',
            'receiving_epa'
        ]
    elif position == 'WR':
        columns = [
            'player', 'team', 'week', 'season', 'owner', 'points', 'position',
            'targets', 'receptions', 'Rec Yds', 'Rec TD', 'receiving_fumbles',
            'receiving_fumbles_lost', 'receiving_first_downs', 'receiving_epa',
            'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles', 'rushing_fumbles_lost',
            'rushing_first_downs', 'rushing_epa'
        ]
    elif position == 'TE':
        columns = [
            'player', 'team', 'week', 'season', 'owner', 'points', 'position',
            'targets', 'receptions', 'Rec Yds', 'Rec TD', 'receiving_fumbles',
            'receiving_fumbles_lost', 'receiving_first_downs', 'receiving_epa'
        ]
    else:
        columns = ['player']  # Default case for other positions

    return player_data[columns]