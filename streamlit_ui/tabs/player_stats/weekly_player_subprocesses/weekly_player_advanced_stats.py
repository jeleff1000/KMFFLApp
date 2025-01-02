import pandas as pd

def get_advanced_stats(player_data, position):
    if position == 'QB':
        columns = [
            'player', 'team', 'week', 'season', 'owner', 'points', 'position',
            'Pass Yds', 'Pass TD', 'completions', 'attempts', 'Int', 'sack_yards',
            'sack_fumbles', 'passing_2pt_conversions', 'passing_air_yards',
            'passing_yards_after_catch', 'passing_first_downs', 'passing_epa',
            'dakota', 'pacr', 'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles',
            'rushing_fumbles_lost', 'rushing_first_downs', 'rushing_epa'
        ]
    elif position == 'RB':
        columns = [
            'player', 'team', 'week', 'season', 'owner', 'points', 'position',
            'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles', 'rushing_fumbles_lost',
            'rushing_first_downs', 'rushing_epa', 'Rec', 'Rec Yds',
            'Rec TD', 'Targets', 'receiving_fumbles', 'receiving_fumbles_lost', 'receiving_first_downs',
            'receiving_epa', 'target_share', 'wopr', 'racr', 'receiving_2pt_conversions',
            'receiving_air_yards', 'receiving_yards_after_catch', 'air_yards_share'
        ]
    elif position in ['WR', 'TE']:
        columns = [
            'player', 'team', 'week', 'season', 'owner', 'points', 'position',
            'Rec', 'Rec Yds', 'Rec TD', 'Targets', 'receiving_fumbles',
            'receiving_fumbles_lost', 'receiving_first_downs', 'receiving_epa',
            'target_share', 'wopr', 'racr', 'receiving_2pt_conversions',
            'receiving_air_yards', 'receiving_yards_after_catch', 'air_yards_share',
            'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles', 'rushing_fumbles_lost',
            'rushing_first_downs', 'rushing_epa'
        ]
    elif position == 'DEF':
        columns = [
            'player', 'team', 'week', 'season', 'owner', 'points', 'position',
            'Def Yds Allow', 'Fum Rec', 'Fum Ret TD', 'Pts Allow', 'Pts Allow 0',
            'Pts Allow 1-6', 'Pts Allow 14-20', 'Pts Allow 21-27', 'Pts Allow 28-34',
            'Pts Allow 35+', 'Pts Allow 7-13', 'Yds Allow 0-99', 'Yds Allow 100-199',
            'Yds Allow 200-299', 'Yds Allow 300-399', 'Yds Allow 400-499', 'Yds Allow 500+',
            'defensive_td', 'Safe', 'Defensive Interceptions', 'Eligible_Defensive_Points_Allowed',
            'Extra Point Return TD', '3 and Outs', '4 Dwn Stops', 'blocked_kick',
            'Muffed Punt Recoveries', 'qb_hit', 'Sack', 'combined tfl and sacks',
            'defensive_extra_point_conv', 'XPR', 'Total Points Allowed', 'TFL', 'Muffed Punts'
        ]
    else:
        columns = ['player', 'team', 'week', 'season', 'owner', 'points', 'position'] # Default case for other positions

    return player_data[columns]