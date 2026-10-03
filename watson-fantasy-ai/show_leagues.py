#!/usr/bin/env python3
"""Simple data viewer with direct output"""
import sys
sys.stdout.flush()

from pathlib import Path
from tinydb import TinyDB

db_path = Path.home() / ".watson" / "historical_data.json"
print("Loading data...", flush=True)

db = TinyDB(db_path)
table = db.table("snapshots")
all_data = table.all()

print(f"\n🏈 WATSON LEAGUE DATA", flush=True)
print(f"{'='*60}", flush=True)
print(f"Total snapshots stored: {len(all_data)}\n", flush=True)

for i, snap in enumerate(all_data, 1):
    season = snap.get("season")
    standings = snap.get("standings", [])
    matchups = snap.get("matchups", [])

    print(f"{i}. Season {season}", flush=True)
    print(f"   Teams: {len(standings)}", flush=True)

    # Show standings
    for team in sorted(standings, key=lambda x: x['wins'], reverse=True)[:5]:
        print(f"     {team['team_name']:30} {team['wins']:2}-{team['losses']:<2} {team['points_for']:7.1f} pts", flush=True)

    print(f"   Matchups: {len(matchups)}", flush=True)
    print()

db.close()
print("✅ Done!", flush=True)

