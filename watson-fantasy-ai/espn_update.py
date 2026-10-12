#!/usr/bin/env python3
"""Refresh current-season ESPN data (actual scores, standings) into the Watson DB.

ESPN is the official league source; run this before any Sleeper sync.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from espn_api.football import League
from tinydb import TinyDB, Query

load_dotenv()
load_dotenv(Path(__file__).resolve().parent / "credentials")

LEAGUE_ID = int(os.getenv("LEAGUE_ID", "2064790109"))
DB_PATH = Path.home() / ".watson" / "historical_data.json"


def _lineup(players):
    return [
        {
            "name": getattr(p, "name", None),
            "position": getattr(p, "position", None),
            "points": getattr(p, "points", 0),
            "projected_points": getattr(p, "projected_points", 0) or 0,
            "slot": getattr(p, "slot_position", None),
        }
        for p in players
    ]


def update_season(year: int) -> dict:
    league = League(
        league_id=LEAGUE_ID,
        year=year,
        espn_s2=os.getenv("ESPN_S2") or None,
        swid=os.getenv("SWID") or None,
    )
    week = league.current_week

    standings = [
        {
            "team_id": t.team_id,
            "team_name": t.team_name,
            "wins": t.wins,
            "losses": t.losses,
            "points_for": t.points_for,
        }
        for t in league.standings()
    ]

    matchups = []
    for w in range(1, week + 1):
        for game in league.box_scores(week=w):
            matchups.append({
                "week": w,
                "home_team": getattr(game.home_team, "team_name", None),
                "home_score": game.home_score,
                "home_projection": getattr(game, "home_projected", 0),
                "home_players": _lineup(getattr(game, "home_lineup", [])),
                "away_team": getattr(game.away_team, "team_name", None),
                "away_score": game.away_score,
                "away_projection": getattr(game, "away_projected", 0),
                "away_players": _lineup(getattr(game, "away_lineup", [])),
            })

    snapshot = {
        "league_id": str(LEAGUE_ID),
        "season": year,
        "standings": standings,
        "matchups": matchups,
        "source": "espn-api-live",
    }

    db = TinyDB(DB_PATH)
    snaps = db.table("snapshots")
    Snap = Query()
    snaps.upsert(snapshot, Snap.season == year)
    db.close()
    return {"season": year, "week": week, "matchups": len(matchups)}


if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    print(f"📡 Pulling live ESPN data for season {year} (league {LEAGUE_ID})...")
    result = update_season(year)
    print(f"✅ Updated season {result['season']}: {result['matchups']} matchups through week {result['week']}")
