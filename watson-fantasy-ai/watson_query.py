#!/usr/bin/env python3
"""
NoSQL Query Interface for Watson League Data
Personal use - query and analyze your league data easily
"""

from pathlib import Path
from tinydb import TinyDB, Query
from typing import List, Dict, Any

class WatsonLeagueDB:
    def __init__(self):
        self.db_path = Path.home() / ".watson" / "historical_data.json"
        self.db = TinyDB(self.db_path)
        self.snapshots = self.db.table("snapshots")

    def get_seasons(self) -> List[int]:
        """Get all available seasons"""
        all_data = self.snapshots.all()
        return sorted(list(set(s.get("season") for s in all_data)))

    def get_season_data(self, season: int) -> Dict[str, Any]:
        """Get all data for a specific season"""
        Snap = Query()
        results = self.snapshots.search(Snap.season == season)
        return results[0] if results else None

    def get_team_record(self, season: int, team_name: str) -> Dict[str, Any]:
        """Get a team's record for a season"""
        data = self.get_season_data(season)
        if not data:
            return None

        for team in data.get("standings", []):
            if team["team_name"].lower() == team_name.lower():
                return team
        return None

    def get_standings(self, season: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get standings for a season (sorted by wins)"""
        data = self.get_season_data(season)
        if not data:
            return []

        standings = data.get("standings", [])
        return sorted(standings, key=lambda x: x["wins"], reverse=True)[:limit]

    def get_matchups(self, season: int) -> List[Dict[str, Any]]:
        """Get all matchups for a season"""
        data = self.get_season_data(season)
        return data.get("matchups", []) if data else []

    def get_available_players(self, season: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get available players for a season"""
        data = self.get_season_data(season)
        if not data:
            return []
        return data.get("available_players", [])[:limit]

    def print_season_summary(self, season: int):
        """Print a nice summary of a season"""
        standings = self.get_standings(season)
        matchups = self.get_matchups(season)

        print(f"\n{'='*70}")
        print(f"SEASON {season} SUMMARY")
        print(f"{'='*70}\n")

        print("STANDINGS:")
        print(f"{'Rank':<6} {'Team':<30} {'Record':<10} {'Points'}")
        print("-" * 70)
        for i, team in enumerate(standings, 1):
            record = f"{team['wins']}-{team['losses']}"
            print(f"{i:<6} {team['team_name']:<30} {record:<10} {team['points_for']:.1f}")

        print(f"\n\nMATCHUPS: {len(matchups)} games")
        for i, match in enumerate(matchups, 1):
            print(f"  {i}. {match['home_team']} ({match['home_score']}) vs {match['away_team']} ({match['away_score']})")

        print(f"\n{'='*70}\n")

    def close(self):
        self.db.close()


if __name__ == "__main__":
    db = WatsonLeagueDB()

    # Show all available seasons
    seasons = db.get_seasons()
    print(f"\n📊 Available Seasons: {seasons}")

    # Show latest season summary
    if seasons:
        latest = max(seasons)
        db.print_season_summary(latest)

    db.close()

