# career_player_matchup_stats.py
import pandas as pd

def get_matchup_stats(player_data):
    data = {
        'Player': player_data['player']
    }
    df = pd.DataFrame(data)
    return df