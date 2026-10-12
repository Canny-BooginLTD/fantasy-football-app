"""Optional ESPN historical data ingestion using espn-api."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from espn_api.football import League
except ModuleNotFoundError:  # pragma: no cover - exercised when optional dep is missing
    League = None

from watson.config import ESPN_PASSWORD, ESPN_S2, ESPN_USERNAME, HISTORICAL_END_YEAR, HISTORICAL_START_YEAR, SWID

logger = logging.getLogger(__name__)


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
        seasons = self._season_range()
        logger.info(f"Starting ESPN historical data scrape for {len(seasons)} season(s): {seasons}")

        for season in seasons:
            try:
                logger.info(f"Fetching data for season {season}...")
                league = self._build_league(season)

                # Fetch standings
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
                logger.info(f"  ✓ Fetched {len(standings)} team standings")

                # Fetch box scores with player details AND PROJECTIONS
                box_scores = []
                for game in league.box_scores():
                    # Get home team players with projections
                    home_players = []
                    if hasattr(game, 'home_lineup'):
                        for player in game.home_lineup:
                            # Try multiple attribute names for projections
                            proj = getattr(player, "projected_points", None) or \
                                   getattr(player, "proPoints", None) or \
                                   getattr(player, "projection", None) or 0
                            home_players.append({
                                "name": getattr(player, "name", None),
                                "position": getattr(player, "position", None),
                                "points": getattr(player, "points", None),
                                "projected_points": proj,
                                "slot": getattr(player, "slot", None),
                            })

                    # Get away team players with projections
                    away_players = []
                    if hasattr(game, 'away_lineup'):
                        for player in game.away_lineup:
                            # Try multiple attribute names for projections
                            proj = getattr(player, "projected_points", None) or \
                                   getattr(player, "proPoints", None) or \
                                   getattr(player, "projection", None) or 0
                            away_players.append({
                                "name": getattr(player, "name", None),
                                "position": getattr(player, "position", None),
                                "points": getattr(player, "points", None),
                                "projected_points": proj,
                                "slot": getattr(player, "slot", None),
                            })

                    # Calculate team projections
                    home_projection = sum(p.get('projected_points', 0) for p in home_players)
                    away_projection = sum(p.get('projected_points', 0) for p in away_players)

                    box_scores.append({
                        "home_team": getattr(game.home_team, "team_name", None),
                        "home_score": getattr(game, "home_score", None),
                        "home_projection": home_projection,
                        "home_players": home_players,
                        "away_team": getattr(game.away_team, "team_name", None),
                        "away_score": getattr(game, "away_score", None),
                        "away_projection": away_projection,
                        "away_players": away_players,
                    })
                logger.info(f"  ✓ Fetched {len(box_scores)} matchup records with player projections")

                # Fetch free agents
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
                logger.info(f"  ✓ Fetched {len(free_agents)} available players")

                # Build player data
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
                logger.info(f"✓ Season {season} data collected successfully")

            except Exception as e:
                logger.error(f"✗ Error fetching season {season}: {str(e)}", exc_info=True)
                continue

        logger.info(f"✓ Scraping complete! Collected {len(snapshots)}/{len(seasons)} seasons")
        return snapshots
