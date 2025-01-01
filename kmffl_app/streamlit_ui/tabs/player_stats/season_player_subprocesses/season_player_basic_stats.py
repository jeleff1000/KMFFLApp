# season_player_basic_stats.py

import pandas as pd

def get_basic_stats():
    # Replace with actual logic to get basic stats
    data = {
        'Player': ['Player1', 'Player2', 'Player3'],
        'Games Played': [10, 12, 8],
        'Points': [150, 200, 120]
    }
    df = pd.DataFrame(data)
    return df