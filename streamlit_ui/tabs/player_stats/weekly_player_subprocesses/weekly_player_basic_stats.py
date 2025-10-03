import pandas as pd

def get_basic_stats(player_data, position):
    if position in ['QB']:
        columns = ['player', 'nfl_team', 'week', 'year', 'manager', 'points', 'nfl_position', 'Pass Yds', 'Pass TD', 'Int', 'Rush Yds', 'Rush TD']
    elif position in ['RB', 'W/R/T']:
        columns = ['player', 'nfl_team', 'week', 'year', 'manager', 'points', 'nfl_position', 'Rush Yds', 'Rush TD', 'Rec', 'Rec Yds', 'Rec TD']
    elif position in ['WR', 'TE']:
        columns = ['player', 'nfl_team', 'week', 'year', 'manager', 'points', 'nfl_position', 'Rec', 'Rec Yds', 'Rec TD', 'Rush Yds', 'Rush TD']
    elif position in ['K']:
        columns = ['player', 'nfl_team', 'week', 'year', 'manager', 'points', 'nfl_position', 'FG Yds', 'FG%', 'field_goal_result', 'field_goal_attempt', 'PAT Made', 'extra_point_attempt']
    elif position in ['DEF']:
        columns = ['player', 'nfl_team', 'week', 'year', 'manager', 'points', 'nfl_position', 'Def Yds Allow', 'Fum Rec', 'Pts Allow', 'defensive_td', 'Safe', 'Defensive Interceptions', 'Eligible_Defensive_Points_Allowed', '3 and Outs', '4 Dwn Stops', 'Sack', 'combined tfl and sacks']
    else:
        columns = ['player', 'nfl_team', 'week', 'year', 'manager', 'points', 'nfl_position']

    player_data['year'] = player_data['year'].astype(str)
    player_data['week'] = player_data['week'].astype(int)
    player_data['points'] = player_data['points'].astype(float)

    sorted_data = player_data.sort_values(['year', 'week', 'points'], ascending=[True, True, False])
    return sorted_data[columns]