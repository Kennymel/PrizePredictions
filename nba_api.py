# scrape_nba_logs_api.py

import os
import pandas as pd
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import time

# Folder to save logs
LOG_DIR = "nba_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Player names exactly as in nba_api
TARGET_PLAYERS = [
    "LeBron James", "Anthony Davis", "D'Angelo Russell", "Austin Reaves", "Rui Hachimura",
    "Jayson Tatum", "Jaylen Brown", "Jrue Holiday", "Derrick White", "Kristaps Porzingis",
    "Nikola Jokic", "Jamal Murray", "Michael Porter Jr.", "Aaron Gordon", "Kentavious Caldwell-Pope",
    "Stephen Curry", "Klay Thompson", "Draymond Green", "Andrew Wiggins", "Kevon Looney"
]

def fetch_recent_games(player_name, num_games=10):
    player = players.find_players_by_full_name(player_name)
    if not player:
        print(f"Player not found: {player_name}")
        return None
    player_id = player[0]['id']
    logs = playergamelog.PlayerGameLog(player_id=player_id, season='2023-24', season_type_all_star='Regular Season')
    df = logs.get_data_frames()[0]
    df = df.head(num_games)
    return df

# Loop through players and save CSVs
for name in TARGET_PLAYERS:
    try:
        df = fetch_recent_games(name, num_games=10)
        if df is not None:
            filename = f"{name.replace(' ', '_')}.csv"
            df.to_csv(os.path.join(LOG_DIR, filename), index=False)
            print(f"Saved: {filename}")
        time.sleep(1)  # avoid rate-limiting
    except Exception as e:
        print(f"Error with {name}: {e}")
