#!/usr/bin/env python3
"""View detailed matchup info with player stats"""
import sys
from watson_query import WatsonLeagueDB

def view_matchup_details(season):
    db = WatsonLeagueDB()
    matchups = db.get_matchups(season)

    print(f"\n{'='*100}")
    print(f"SEASON {season} - DETAILED MATCHUPS")
    print(f"{'='*100}\n")

    if not matchups:
        print(f"No matchups found for season {season}")
    else:
        for i, match in enumerate(matchups, 1):
            home_team = match['home_team']
            home_score = match['home_score']
            away_team = match['away_team']
            away_score = match['away_score']
            home_players = match.get('home_players', [])
            away_players = match.get('away_players', [])

            winner = home_team if home_score > away_score else away_team

            print(f"MATCHUP {i}: {home_team} ({home_score:.2f}) vs {away_team} ({away_score:.2f})")
            print(f"{'Winner: ' + winner}")
            print("-" * 100)

            # Home team players
            print(f"\n{home_team}:")
            if home_players:
                print(f"{'Player':<30} {'Position':<12} {'Points':>10}")
                print("-" * 52)
                for player in home_players:
                    name = player.get('name', 'N/A')
                    pos = player.get('position', 'N/A')
                    pts = player.get('points', 0)
                    print(f"{name:<30} {pos:<12} {pts:>10.2f}")
            else:
                print("  (No player data available)")

            # Away team players
            print(f"\n{away_team}:")
            if away_players:
                print(f"{'Player':<30} {'Position':<12} {'Points':>10}")
                print("-" * 52)
                for player in away_players:
                    name = player.get('name', 'N/A')
                    pos = player.get('position', 'N/A')
                    pts = player.get('points', 0)
                    print(f"{name:<30} {pos:<12} {pts:>10.2f}")
            else:
                print("  (No player data available)")

            print(f"\n{'='*100}\n")

    db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python view_matchup_details.py <season>")
        print("Example: python view_matchup_details.py 2022")
        sys.exit(1)

    season = int(sys.argv[1])
    view_matchup_details(season)

