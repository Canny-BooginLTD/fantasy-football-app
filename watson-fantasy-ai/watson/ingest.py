"""ESPN historical data ingestion entrypoint."""

from __future__ import annotations

import argparse
from typing import Optional

from watson.espn_scraper import EspnHistoricalDataScraper
from watson.history_store import HistoricalDataStore


def ingest_espn_history(league_id: str, year: Optional[int] = None, storage_path: Optional[str] = None):
    """Fetch ESPN historical data with espn-api and persist it locally."""
    scraper = EspnHistoricalDataScraper(league_id=league_id, year=year)
    store = HistoricalDataStore(storage_path=storage_path)
    snapshots = scraper.scrape_historical_snapshots()
    store.save_snapshots(snapshots)
    return snapshots


def main():
    parser = argparse.ArgumentParser(description="Import ESPN historical fantasy data into local storage")
    parser.add_argument("league_id", help="ESPN league ID")
    parser.add_argument("--year", type=int, default=None, help="Optional single season to import")
    parser.add_argument("--storage-path", default=None, help="Optional path for local storage")
    args = parser.parse_args()

    snapshots = ingest_espn_history(args.league_id, year=args.year, storage_path=args.storage_path)
    print(f"Imported {len(snapshots)} snapshot(s) for league {args.league_id}")
    return snapshots


if __name__ == "__main__":
    main()
