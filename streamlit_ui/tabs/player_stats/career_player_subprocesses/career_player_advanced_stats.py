import pandas as pd

def get_advanced_stats(player_data, position):
    if position == 'QB':
        columns = [
            'player', 'nfl_team', 'owner', 'points', 'nfl_position',
            'Pass Yds', 'completions', 'attempts', 'Pass TD', 'Int', 'sack_yards',
            'sack_fumbles', 'passing_2pt_conversions', 'passing_air_yards',
            'passing_yards_after_catch', 'passing_first_downs', 'passing_epa',
            'dakota', 'pacr', 'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles',
            'rushing_fumbles_lost', 'rushing_first_downs', 'rushing_epa'
        ]
    elif position == 'RB':
        columns = [
            'player', 'nfl_team', 'owner', 'points', 'nfl_position',
            'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles', 'rushing_fumbles_lost',
            'rushing_first_downs', 'rushing_epa', 'Rec', 'Rec Yds',
            'Rec TD', 'Targets', 'receiving_fumbles', 'receiving_fumbles_lost', 'receiving_first_downs',
            'receiving_epa', 'target_share', 'wopr', 'racr', 'receiving_2pt_conversions',
            'receiving_air_yards', 'receiving_yards_after_catch', 'air_yards_share'
        ]
    elif position in ['WR', 'TE']:
        columns = [
            'player', 'nfl_team', 'owner', 'points', 'nfl_position',
            'Rec', 'Rec Yds', 'Rec TD', 'Targets', 'receiving_fumbles',
            'receiving_fumbles_lost', 'receiving_first_downs', 'receiving_epa',
            'target_share', 'wopr', 'racr', 'receiving_2pt_conversions',
            'receiving_air_yards', 'receiving_yards_after_catch', 'air_yards_share',
            'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles', 'rushing_fumbles_lost',
            'rushing_first_downs', 'rushing_epa'
        ]
    elif position == 'DEF':
        columns = [
            'player', 'nfl_team', 'owner', 'points', 'nfl_position',
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
        columns = ['player', 'nfl_team', 'owner', 'points', 'nfl_position']

    existing_columns = [col for col in columns if col in player_data.columns]
    player_data = player_data[existing_columns]

    agg_funcs = {col: 'sum' if col not in ['nfl_team', 'owner', 'nfl_position'] else 'first' for col in existing_columns}

    aggregated_data = player_data.groupby(['player', 'nfl_position']).agg(agg_funcs)

    columns_to_drop = [col for col in ['player', 'nfl_position'] if col in aggregated_data.columns]
    if columns_to_drop:
        aggregated_data = aggregated_data.drop(columns=columns_to_drop)

    aggregated_data = aggregated_data.reset_index()

    return aggregated_data