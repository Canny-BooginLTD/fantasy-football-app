"""League data adapter for Watson"""

from copy import deepcopy
from typing import Any, Dict, Optional


class LeagueClient:
    def __init__(self, league_id: Any, source_name: str = "local", local_mode: bool = True, seed_data: Optional[Dict[str, Any]] = None):
        self.league_id = league_id
        self.source_name = source_name
        self.local_mode = local_mode
        self._seed_data = seed_data or self._default_seed_data()

    def get_league_data(self):
        """Fetch league standings and metadata from the configured source."""
        data = deepcopy(self._seed_data)
        data.setdefault("league_id", self.league_id)
        data.setdefault("source_name", self.source_name)
        data.setdefault("local_mode", self.local_mode)
        return data

    def get_rosters(self):
        """Fetch all team rosters."""
        league_data = self.get_league_data()
        return league_data.get("teams", []) if league_data else None

    def get_players(self):
        """Fetch available players and their stats."""
        league_data = self.get_league_data()
        return league_data.get("players", []) if league_data else None

    def _default_seed_data(self):
        return {
            "teams": [
                {
                    "id": 1,
                    "strength": "balanced",
                    "roster": [
                        {"player_id": 101, "name": "Sample QB", "position": "QB", "projected_points": 22.1, "trade_value": 18, "market_position": "starter"},
                        {"player_id": 102, "name": "Sample RB", "position": "RB", "projected_points": 16.4, "trade_value": 20, "market_position": "starter"},
                        {"player_id": 103, "name": "Sample WR", "position": "WR", "projected_points": 14.3, "trade_value": 17, "market_position": "starter"},
                    ],
                }
            ],
            "available_players": [
                {"player_id": 201, "name": "Waiver QB", "position": "QB", "projected_points": 19.2},
                {"player_id": 202, "name": "Waiver RB", "position": "RB", "projected_points": 13.8},
                {"player_id": 203, "name": "Waiver WR", "position": "WR", "projected_points": 12.7},
            ],
            "players": [
                {"player_id": 101, "name": "Sample QB", "position": "QB", "injury_status": "Healthy", "trade_value": 18, "market_position": "starter"},
                {"player_id": 102, "name": "Sample RB", "position": "RB", "injury_status": "Questionable", "trade_value": 20, "market_position": "starter"},
                {"player_id": 103, "name": "Sample WR", "position": "WR", "injury_status": "Out", "trade_value": 17, "market_position": "starter"},
            ],
        }
