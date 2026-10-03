#!/usr/bin/env python3
"""Standalone script to scrape ESPN historical data."""

import logging
import sys
from watson.ingest import ingest_espn_history

# Configure logging to show all output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('watson_scrape.log')
    ]
)

if __name__ == "__main__":
    league_id = "2064790109"

    print("\n" + "="*60)
    print("🏈 Watson ESPN Historical Data Scraper")
    print("="*60)
    print(f"League ID: {league_id}")
    print("="*60 + "\n")

    # Scrape multiple years
    for year in range(2020, 2025):
        print(f"\n📅 Scraping {year}...")
        try:
            snapshots = ingest_espn_history(league_id, year=year)
            if snapshots:
                print(f"✓ Successfully scraped {year}")
            else:
                print(f"⚠️ No data for {year}")
        except Exception as e:
            print(f"✗ Error scraping {year}: {e}")

    print("\n" + "="*60)
    print("✓ Scraping Complete!")
    print("="*60 + "\n")

