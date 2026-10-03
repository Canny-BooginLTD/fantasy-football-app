#!/usr/bin/env python3
"""Grab all historical data NOW - personal use only"""

import sys
from watson.ingest import ingest_espn_history

LEAGUE_ID = "2064790109"

print("\n🏈 Grabbing all historical data...\n")

try:
    snapshots = ingest_espn_history(LEAGUE_ID)
    print(f"\n✅ DONE! Grabbed {len(snapshots)} season(s) of data")
    print(f"📍 Stored at: ~/.watson/historical_data.json\n")
except Exception as e:
    print(f"\n❌ Error: {e}\n")
    sys.exit(1)

