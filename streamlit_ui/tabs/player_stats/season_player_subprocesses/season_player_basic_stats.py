import pandas as pd

def get_basic_stats(player_data, position):
    if position in ['QB']:
        columns = ['player', 'team', 'season', 'owner', 'points', 'position', 'Pass Yds', 'Pass TD', 'Int', 'Rush Yds', 'Rush TD']
    elif position in ['RB', 'W/R/T']:
        columns = ['player', 'team', 'season', 'owner', 'points', 'position', 'Rush Yds', 'Rush TD', 'Rec', 'Rec Yds', 'Rec TD']
    elif position in ['WR', 'TE']:
        columns = ['player', 'team', 'season', 'owner', 'points', 'position', 'Rec', 'Rec Yds', 'Rec TD', 'Rush Yds', 'Rush TD']
    elif position in ['K']:
        columns = ['player', 'team', 'season', 'owner', 'points', 'position', 'FG Yds', 'FG%', 'field_goal_result', 'field_goal_attempt', 'PAT Made', 'extra_point_attempt']
    elif position in ['DEF']:
        columns = ['player', 'team', 'season', 'owner', 'points', 'position', 'Def Yds Allow', 'Fum Rec', 'Pts Allow', 'defensive_td', 'Safe', 'Defensive Interceptions', 'Eligible_Defensive_Points_Allowed', '3 and Outs', '4 Dwn Stops', 'Sack', 'combined tfl and sacks']
    else:
        columns = ['player', 'team', 'season', 'owner', 'points', 'position']

    # Filter out columns that do not exist in the player_data
    existing_columns = [col for col in columns if col in player_data.columns]
    player_data = player_data[existing_columns]

    # Define aggregation functions for existing columns
    agg_funcs = {col: 'sum' if col not in ['team', 'owner', 'position'] else 'first' for col in existing_columns}
    if 'FG%' in existing_columns:
        agg_funcs['FG%'] = 'mean'

    # Aggregate data by player and season
    aggregated_data = player_data.groupby(['player', 'season', 'position']).agg(agg_funcs)

    # Drop the 'player' and 'season' columns if they exist before resetting the index
    columns_to_drop = [col for col in ['player', 'season', 'position'] if col in aggregated_data.columns]
    if columns_to_drop:
        aggregated_data = aggregated_data.drop(columns=columns_to_drop)

    # Reset index without inserting existing columns
    aggregated_data = aggregated_data.reset_index()

    # Format the 'season' column as a string without commas
    if 'season' in aggregated_data.columns:
        aggregated_data['season'] = aggregated_data['season'].astype(str).str.replace(',', '')

    return aggregated_data