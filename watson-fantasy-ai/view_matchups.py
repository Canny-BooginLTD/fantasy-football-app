#!/usr/bin/env python3
"""View matchups from a specific season"""
import sys
from watson_query import WatsonLeagueDB

def view_matchups(season):
    db = WatsonLeagueDB()
    matchups = db.get_matchups(season)

    print(f"\n{'='*70}")
    print(f"SEASON {season} MATCHUPS")
    print(f"{'='*70}\n")

    if not matchups:
        print(f"No matchups found for season {season}")
    else:
        print(f"Total Matchups: {len(matchups)}\n")
        for i, match in enumerate(matchups, 1):
            home = match['home_team']
            home_score = match['home_score']
            away = match['away_team']
            away_score = match['away_score']

            winner = home if home_score > away_score else away
            print(f"{i}. {home:<30} {home_score:>6.2f}")
            print(f"   vs")
            print(f"   {away:<30} {away_score:>6.2f}")
            print()

    db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python view_matchups.py <season>")
        print("Example: python view_matchups.py 2022")
        sys.exit(1)

    season = int(sys.argv[1])
    view_matchups(season)

