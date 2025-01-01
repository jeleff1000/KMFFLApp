# career_player_basic_stats.py
import pandas as pd

def get_basic_stats(player_data):
    return player_data[['player', 'points']]