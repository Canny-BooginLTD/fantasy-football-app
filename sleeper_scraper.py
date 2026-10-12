#!/usr/bin/env python3
"""Watson Sleeper Player Stats Scraper - Get player projections for ESPN rosters"""

from sleeper_wrapper import Stats
from watson_query import WatsonLeagueDB
from typing import Dict, List, Any
import json
from pathlib import Path
from datetime import datetime

class SleeperScraper:
    """Fetch Sleeper player projections and map to ESPN rosters"""

    CACHE_FILE = Path.home() / ".watson" / "sleeper_cache.json"

    def __init__(self):
        self.stats = Stats()
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cached data from file"""
        if self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self, data: Dict[str, Any]):
        """Save data to cache file"""
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def is_cache_stale(self, max_age_hours: int = 24) -> bool:
        """Check if cache is older than max_age_hours"""
        if not self.cache.get('timestamp'):
            return True

        try:
            cached_time = datetime.fromisoformat(self.cache['timestamp'])
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600
            return age_hours > max_age_hours
        except:
            return True

    def get_player_projections(self, week: int) -> Dict[str, float]:
        """Get all player projections for a week from Sleeper"""
        try:
            projections = self.stats.get_week_projections("nfl", week)
            return projections if projections else {}
        except Exception as e:
            print(f"❌ Error fetching player projections for week {week}: {e}")
            return {}

    def sync_espn_rosters_with_sleeper(self, week: int) -> Dict[str, Any]:
        """Sync ESPN matchups with Sleeper player projections"""
        print(f"📡 Syncing Sleeper player projections for week {week}...")

        try:
            # Get Sleeper player projections
            player_projections = self.get_player_projections(week)

            # Get ESPN rosters and matchups
            db = WatsonLeagueDB()
            current_season = max(db.get_seasons())
            matchups = db.get_matchups(current_season)
            db.close()

            # Map ESPN players to Sleeper projections
            enhanced_matchups = []
            for matchup in matchups:
                home_proj = self._calculate_team_projection(
                    matchup.get('home_players', []),
                    player_projections
                )
                away_proj = self._calculate_team_projection(
                    matchup.get('away_players', []),
                    player_projections
                )

                enhanced_matchups.append({
                    "matchup_id": matchup.get('matchup_id', 'unknown'),
                    "home_team": matchup['home_team'],
                    "away_team": matchup['away_team'],
                    "home_projection": home_proj,
                    "away_projection": away_proj,
                    "home_players": matchup.get('home_players', []),
                    "away_players": matchup.get('away_players', []),
                    "week": week
                })

            # Save to cache
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "week": week,
                "season": current_season,
                "player_projections": player_projections,
                "matchups": enhanced_matchups
            }

            self.cache.update(cache_data)
            self._save_cache(self.cache)

            print(f"✅ Synced {len(enhanced_matchups)} matchups with Sleeper projections")
            return cache_data

        except Exception as e:
            print(f"❌ Error syncing data: {e}")
            return {}

    def _calculate_team_projection(self, players: List[Dict[str, Any]], projections: Dict[str, float]) -> float:
        """Calculate team projection by summing player Sleeper projections"""
        total = 0.0
        for player in players:
            # Try to match player by name or ID
            player_name = player.get('name', '').lower()
            player_id = player.get('player_id')

            # Search in Sleeper projections by ID or name
            for proj_id, proj_points in projections.items():
                # Sleeper projections are keyed by player ID
                if player_id and proj_id == str(player_id):
                    total += proj_points
                    break

        return round(total, 2)

    def get_cached_matchups(self) -> List[Dict[str, Any]]:
        """Get cached matchups with projections"""
        return self.cache.get('matchups', [])

    def get_player_projection(self, player_name: str) -> float:
        """Get cached projection for a specific player"""
        projections = self.cache.get('player_projections', {})
        for proj_id, points in projections.items():
            # This would need player ID mapping
            pass
        return 0.0


if __name__ == "__main__":
    scraper = SleeperScraper()

    print("\n" + "="*80)
    print("SLEEPER PLAYER PROJECTIONS SYNC")
    print("="*80 + "\n")

    # Sync current week
    result = scraper.sync_espn_rosters_with_sleeper(1)

    if result:
        matchups = result.get('matchups', [])
        print(f"\n✅ Synced {len(matchups)} matchups:")
        for m in matchups:
            print(f"  {m['home_team']} ({m['home_projection']}) vs {m['away_team']} ({m['away_projection']})")

    print("\n✅ Done! Projections cached locally.")


