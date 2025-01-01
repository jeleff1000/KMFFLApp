import pandas as pd

def get_basic_stats(player_data, position):
    if position in ['QB']:
        columns = ['player', 'team', 'week', 'season', 'owner', 'points', 'position', 'Pass Yds', 'Int Pass TD', 'Rush Yds', 'Rush TD']
    elif position in ['RB', 'W/R/T']:
        columns = ['player', 'team', 'week', 'season', 'owner', 'points', 'position', 'Rush Yds', 'Rush TD', 'Rec Yds', 'Rec TD']
    elif position in ['WR']:
        columns = ['player', 'team', 'week', 'season', 'owner', 'points', 'position', 'Rec Yds', 'Rec TD', 'Rush Yds', 'Rush TD']
    elif position in ['K']:
        columns = ['player', 'team', 'week', 'season', 'owner', 'points', 'position', 'FG Yds', 'FG%', 'field_goal_result', 'field_goal_attempt', 'PAT Made', 'extra_point_attempt']
    elif position in ['DEF']:
        columns = ['player', 'team', 'week', 'season', 'owner', 'points', 'position', 'Def Yds Allow', 'Fum Rec', 'Pts Allow', 'defensive_td', 'Safe', 'Defensive Interceptions', 'Eligible_Defensive_Points_Allowed', '3 and Outs', '4 Dwn Stops', 'Sack', 'combined tfl and sacks']
    else:
        columns = ['player', 'team', 'week', 'season', 'owner', 'points', 'position']

    player_data['season'] = player_data['season'].astype(str).str.replace(',', '')
    return player_data[columns]