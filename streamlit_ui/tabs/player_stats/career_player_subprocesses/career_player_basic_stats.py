import pandas as pd

def get_basic_stats(player_data, position):
    if position in ['QB']:
        columns = ['player', 'nfl_team', 'owner', 'points', 'nfl_position', 'Pass Yds', 'Pass TD', 'Int', 'Rush Yds', 'Rush TD']
    elif position in ['RB', 'W/R/T']:
        columns = ['player', 'nfl_team', 'owner', 'points', 'nfl_position', 'Rush Yds', 'Rush TD', 'Rec', 'Rec Yds', 'Rec TD']
    elif position in ['WR', 'TE']:
        columns = ['player', 'nfl_team', 'owner', 'points', 'nfl_position', 'Rec', 'Rec Yds', 'Rec TD', 'Rush Yds', 'Rush TD']
    elif position in ['K']:
        columns = ['player', 'nfl_team', 'owner', 'points', 'nfl_position', 'FG Yds', 'FG%', 'field_goal_result', 'field_goal_attempt', 'PAT Made', 'extra_point_attempt']
    elif position in ['DEF']:
        columns = ['player', 'nfl_team', 'owner', 'points', 'nfl_position', 'Def Yds Allow', 'Fum Rec', 'Pts Allow', 'defensive_td', 'Safe', 'Defensive Interceptions', 'Eligible_Defensive_Points_Allowed', '3 and Outs', '4 Dwn Stops', 'Sack', 'combined tfl and sacks']
    else:
        columns = ['player', 'nfl_team', 'owner', 'points', 'nfl_position']

    # Filter out columns that do not exist in the player_data
    existing_columns = [col for col in columns if col in player_data.columns]
    player_data = player_data[existing_columns]

    # Define aggregation functions for existing columns
    agg_funcs = {col: 'sum' if col not in ['nfl_team', 'owner', 'nfl_position'] else 'first' for col in existing_columns}
    if 'FG%' in existing_columns:
        agg_funcs['FG%'] = 'mean'

    # Aggregate data by player and nfl_position
    aggregated_data = player_data.groupby(['player', 'nfl_position']).agg(agg_funcs)

    # Drop the 'player' and 'nfl_position' columns if they exist before resetting the index
    columns_to_drop = [col for col in ['player', 'nfl_position'] if col in aggregated_data.columns]
    if columns_to_drop:
        aggregated_data = aggregated_data.drop(columns=columns_to_drop)

    # Reset index without inserting existing columns
    aggregated_data = aggregated_data.reset_index()

    return aggregated_data