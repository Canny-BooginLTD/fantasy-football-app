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


def fetch_season(year: int) -> dict:
    league = League(
        league_id=LEAGUE_ID,
        year=year,
        espn_s2=os.getenv("ESPN_S2") or None,
        swid=os.getenv("SWID") or None,
    )
    week = league.current_week
    scoring_period = getattr(league, "scoringPeriodId", week)
    matchup_periods = getattr(getattr(league, "settings", None), "matchup_periods", {})

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
        period_end = next((max(period) for period in matchup_periods.values() if w in period), w)
        for game in league.box_scores(week=w):
            matchups.append({
                "week": w,
                "completed": period_end < scoring_period,
                "home_team": getattr(game.home_team, "team_name", None),
                "home_score": game.home_score,
                "home_projection": getattr(game, "home_projected", 0),
                "home_players": _lineup(getattr(game, "home_lineup", [])),
                "away_team": getattr(game.away_team, "team_name", None),
                "away_score": game.away_score,
                "away_projection": getattr(game, "away_projected", 0),
                "away_players": _lineup(getattr(game, "away_lineup", [])),
            })

    # Waiver wire: current free agents with this week's projections.
    # Non-fatal: scores/standings still refresh if this endpoint fails.
    try:
        available_players = [
            {
                "name": p.name,
                "position": getattr(p, "position", None),
                "pro_team": getattr(p, "proTeam", None),
                "injury_status": getattr(p, "injuryStatus", None) or None,
                "points": getattr(p, "points", 0) or 0,
                "projected_points": getattr(p, "projected_points", 0) or 0,
            }
            for p in league.free_agents(week=week, size=100)
        ]
    except Exception as exc:
        print(f"⚠️ Could not fetch free agents: {exc}")
        available_players = []

    snapshot = {
        "league_id": str(LEAGUE_ID),
        "season": year,
        "current_week": week,
        "standings": standings,
        "matchups": matchups,
        "available_players": available_players,
        "source": "espn-api-live",
    }

    return snapshot


def store_season(snapshot: dict) -> dict:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TinyDB(DB_PATH) as db:
        db.table("snapshots").upsert(snapshot, Query().season == snapshot["season"])
    return {"season": snapshot["season"], "week": snapshot["current_week"],
            "matchups": len(snapshot["matchups"])}


def update_season(year: int) -> dict:
    return store_season(fetch_season(year))


if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    print(f"📡 Pulling live ESPN data for season {year} (league {LEAGUE_ID})...")
    result = update_season(year)
    print(f"✅ Updated season {result['season']}: {result['matchups']} matchups through week {result['week']}")
