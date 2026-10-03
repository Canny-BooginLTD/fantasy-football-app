#!/usr/bin/env python3
"""View all historical seasons"""
from watson_query import WatsonLeagueDB

db = WatsonLeagueDB()
seasons = db.get_seasons()

print(f"\n📊 Available Seasons: {seasons}\n")

for season in seasons:
    db.print_season_summary(season)

db.close()

