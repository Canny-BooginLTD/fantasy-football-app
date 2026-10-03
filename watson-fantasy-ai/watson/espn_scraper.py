"""Optional ESPN historical data ingestion using espn-api."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from espn_api.football import League
except ModuleNotFoundError:  # pragma: no cover - exercised when optional dep is missing
    League = None

from watson.config import ESPN_PASSWORD, ESPN_S2, ESPN_USERNAME, HISTORICAL_END_YEAR, HISTORICAL_START_YEAR, SWID


@dataclass
class EspnHistoricalDataScraper:
    """Adapter for fetching ESPN historical league data via espn-api.

    This module is intentionally separate from the main analyzer so ESPN access
    remains an ingestion step only. Put your login details in the repo-root
    `credentials` file and use this class only when importing historical data.
    """

    league_id: str
    year: Optional[int] = None
    headless: bool = True
    username: Optional[str] = ESPN_USERNAME
    password: Optional[str] = ESPN_PASSWORD
    espn_s2: Optional[str] = ESPN_S2
    swid: Optional[str] = SWID

    def _build_league(self, season: int) -> Any:
        if League is None:
            raise ModuleNotFoundError("espn-api is not installed. Install it to ingest ESPN history.")
        return League(
            league_id=int(self.league_id),
            year=season,
            espn_s2=self.espn_s2,
            swid=self.swid,
        )

    def _season_range(self) -> List[int]:
        if self.year:
            return [self.year]
        end_year = int(HISTORICAL_END_YEAR) if HISTORICAL_END_YEAR else datetime.now().year
        return list(range(HISTORICAL_START_YEAR, end_year + 1))

    def scrape_historical_snapshots(self) -> List[Dict[str, Any]]:
        """Return normalized historical snapshots for local storage."""
        snapshots: List[Dict[str, Any]] = []
        for season in self._season_range():
            league = self._build_league(season)
            standings = [
                {
                    "team_id": getattr(team, "team_id", None),
                    "team_name": getattr(team, "team_name", None),
                    "wins": getattr(team, "wins", None),
                    "losses": getattr(team, "losses", None),
                    "points_for": getattr(team, "points_for", None),
                }
                for team in league.standings()
            ]
            box_scores = [
                {
                    "home_team": getattr(game.home_team, "team_name", None),
                    "home_score": getattr(game, "home_score", None),
                    "away_team": getattr(game.away_team, "team_name", None),
                    "away_score": getattr(game, "away_score", None),
                }
                for game in league.box_scores()
            ]
            free_agents = [
                {
                    "player_id": getattr(player, "playerId", None),
                    "name": getattr(player, "name", None),
                    "position": getattr(player, "position", None),
                    "points": getattr(player, "points", None),
                    "projected_points": getattr(player, "projected_points", None),
                }
                for player in league.free_agents(size=10)
            ]
            players = [
                {
                    "player_id": getattr(player, "playerId", None),
                    "name": getattr(player, "name", None),
                    "position": getattr(player, "position", None),
                    "injury_status": getattr(player, "injuryStatus", None),
                    "trade_value": getattr(player, "trade_value", None),
                    "market_position": getattr(player, "status", None),
                    "points": getattr(player, "points", None),
                }
                for player in free_agents
            ]
            snapshots.append(
                {
                    "league_id": self.league_id,
                    "season": season,
                    "standings": standings,
                    "matchups": box_scores,
                    "players": players,
                    "available_players": free_agents,
                    "source": "espn-api",
                }
            )
        return snapshots
