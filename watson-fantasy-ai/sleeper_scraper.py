#!/usr/bin/env python3
"""Watson Sleeper API Scraper - Fetch current season projections (once per week)"""

from sleeper_wrapper import Stats, League
from typing import Dict, List, Any
import json
from pathlib import Path
from datetime import datetime

class SleeperScraper:
    """Fetch current week projections and stats from Sleeper API (cached weekly)"""

    CACHE_FILE = Path.home() / ".watson" / "sleeper_cache.json"

    def __init__(self, league_id: str):
        self.league_id = league_id
        self.stats = Stats()
        self.league = League(league_id)
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

    def get_week_projections(self, week: int) -> Dict[str, float]:
        """Get player projections for a specific week (from cache or API)"""
        # Try cache first
        if f"week_{week}_projections" in self.cache:
            return self.cache[f"week_{week}_projections"]

        # Fetch from API
        try:
            projections = self.stats.get_week_projections("nfl", week)
            return projections if projections else {}
        except Exception as e:
            print(f"Error fetching projections for week {week}: {e}")
            return {}

    def sync_weekly_data(self, week: int) -> Dict[str, Any]:
        """Sync all weekly data from Sleeper API once (call this weekly)"""
        print(f"📡 Syncing Sleeper data for week {week}...")

        try:
            # Fetch all data
            projections = self.stats.get_week_projections("nfl", week)
            stats = self.stats.get_week_stats("nfl", week)
            rosters = self.league.get_rosters()
            matchups = self.league.get_matchups(week)

            # Calculate matchup projections
            matchup_projs = []
            if matchups and projections:
                for matchup in matchups:
                    home_roster = next((r for r in rosters if r['roster_id'] == matchup.get('roster_id')), None)
                    away_roster = next((r for r in rosters if r['roster_id'] == matchup.get('opponent_id')), None)

                    if home_roster and away_roster:
                        home_proj = self._calculate_team_projection(home_roster.get('players', []), projections)
                        away_proj = self._calculate_team_projection(away_roster.get('players', []), projections)

                        matchup_projs.append({
                            "matchup_id": matchup.get('matchup_id'),
                            "home_roster_id": home_roster['roster_id'],
                            "away_roster_id": away_roster['roster_id'],
                            "home_projection": home_proj,
                            "away_projection": away_proj,
                            "week": week
                        })

            # Build cache
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "week": week,
                f"week_{week}_projections": projections or {},
                f"week_{week}_stats": stats or {},
                f"week_{week}_matchups": matchup_projs,
                "rosters": rosters or [],
            }

            # Update and save
            self.cache.update(cache_data)
            self._save_cache(self.cache)

            print(f"✅ Synced {len(matchup_projs)} matchup projections for week {week}")
            return cache_data

        except Exception as e:
            print(f"❌ Error syncing Sleeper data: {e}")
            return {}

    def _calculate_team_projection(self, roster_players: List[Dict[str, Any]], projections: Dict[str, float]) -> float:
        """Calculate total team projection from player projections"""
        total = 0.0
        for player in roster_players:
            player_id = player.get('player_id')
            if player_id and player_id in projections:
                total += projections.get(player_id, 0)
        return round(total, 2)

    def get_matchup_projections(self, week: int) -> List[Dict[str, Any]]:
        """Get cached matchup projections for a week"""
        return self.cache.get(f"week_{week}_matchups", [])

    def get_cached_projection(self, week: int, team_name: str) -> float:
        """Get cached projection for a team (returns 0 if not found)"""
        matchups = self.get_matchup_projections(week)
        # This is a placeholder - in real use, map team_name to roster_id
        return 0.0


if __name__ == "__main__":
    league_id = "YOUR_LEAGUE_ID"
    scraper = SleeperScraper(league_id)

    print("\n" + "="*80)
    print("SLEEPER WEEKLY SYNC")
    print("="*80 + "\n")

    # Sync current week
    scraper.sync_weekly_data(1)

    print("\n✅ Done! Projections cached for offline use.")


