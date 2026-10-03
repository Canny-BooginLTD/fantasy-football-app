#!/usr/bin/env python3
"""Query historical data from TinyDB"""

import tinydb
from pathlib import Path
import json

db_path = Path.home() / ".watson" / "historical_data.json"

print(f"\n📊 Watson Historical Data\n{'='*50}\n")

try:
    db = TinyDB(db_path)
    table = db.table("snapshots")

    snapshots = table.all()
    print(f"✓ Total snapshots: {len(snapshots)}\n")

    for snap in snapshots:
        season = snap.get("season")
        league_id = snap.get("league_id")
        standings = snap.get("standings", [])
        matchups = snap.get("matchups", [])

        print(f"Season {season}:")
        print(f"  Teams: {len(standings)}")
        for team in standings[:3]:  # Show first 3 teams
            print(f"    - {team['team_name']}: {team['wins']}-{team['losses']} ({team['points_for']:.1f} pts)")
        print(f"  Matchups: {len(matchups)}")
        print()

    db.close()

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"DB path: {db_path}")
    print(f"File exists: {db_path.exists()}")

