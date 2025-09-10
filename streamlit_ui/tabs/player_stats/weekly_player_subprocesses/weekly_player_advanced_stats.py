import pandas as pd

def get_advanced_stats(player_data):
    def select_columns(group):
        fantasy_position = group['fantasy position'].iloc[0] if 'fantasy position' in group.columns else None
        if fantasy_position == 'QB':
            columns = [
                'player', 'team', 'week', 'season', 'owner', 'points', 'position',
                'Pass Yds', 'Pass TD', 'completions', 'attempts', 'Int', 'sack_yards',
                'sack_fumbles', 'passing_2pt_conversions', 'passing_air_yards',
                'passing_yards_after_catch', 'passing_first_downs', 'passing_epa',
                'dakota', 'pacr', 'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles',
                'rushing_fumbles_lost', 'rushing_first_downs', 'rushing_epa'
            ]
        elif fantasy_position == 'RB':
            columns = [
                'player', 'team', 'week', 'season', 'owner', 'points', 'position',
                'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles', 'rushing_fumbles_lost',
                'rushing_first_downs', 'rushing_epa', 'Rec', 'Rec Yds',
                'Rec TD', 'Targets', 'receiving_fumbles', 'receiving_fumbles_lost', 'receiving_first_downs',
                'receiving_epa', 'target_share', 'wopr', 'racr', 'receiving_2pt_conversions',
                'receiving_air_yards', 'receiving_yards_after_catch', 'air_yards_share'
            ]
        elif fantasy_position in ['WR', 'TE']:
            columns = [
                'player', 'team', 'week', 'season', 'owner', 'points', 'position',
                'Rec', 'Rec Yds', 'Rec TD', 'Targets', 'receiving_fumbles',
                'receiving_fumbles_lost', 'receiving_first_downs', 'receiving_epa',
                'target_share', 'wopr', 'racr', 'receiving_2pt_conversions',
                'receiving_air_yards', 'receiving_yards_after_catch', 'air_yards_share',
                'Rush Yds', 'Rush Att', 'Rush TD', 'rushing_fumbles', 'rushing_fumbles_lost',
                'rushing_first_downs', 'rushing_epa'
            ]
        elif fantasy_position == 'DEF':
            columns = [
                'player', 'team', 'week', 'season', 'owner', 'points', 'position',
                'Def Yds Allow', 'Fum Rec', 'Fum Ret TD', 'Pts Allow', 'Pts Allow 0',
                'Pts Allow 1-6', 'Pts Allow 14-20', 'Pts Allow 21-27', 'Pts Allow 28-34',
                'Pts Allow 35+', 'Pts Allow 7-13', 'Yds Allow 0-99', 'Yds Allow 100-199',
                'Yds Allow 200-299', 'Yds Allow 300-399', 'Yds Allow 400-499', 'Yds Allow 500+',
                'defensive_td', 'Safe', 'blocked_kick', 'Muffed Punt Recoveries', 'qb_hit',
                'Sack', 'combined tfl and sacks', 'defensive_extra_point_conv',
                'Total Points Allowed', 'Muffed Punts'
            ]
        else:
            columns = ['player', 'team', 'week', 'season', 'owner', 'points', 'position']
        # Only select columns that exist in the group
        columns = [col for col in columns if col in group.columns]
        return group[columns]

    player_data['season'] = player_data['season'].astype(str)
    player_data['week'] = player_data['week'].astype(int)
    player_data['points'] = player_data['points'].astype(float)

    sorted_data = player_data.sort_values(['season', 'week', 'points'], ascending=[True, True, False])
    result = sorted_data.groupby('fantasy position', group_keys=False).apply(select_columns)
    result = result.sort_values(['season', 'week', 'points'], ascending=[True, True, False]).reset_index(drop=True)
    return result