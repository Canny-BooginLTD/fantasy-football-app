"""Watson main application"""

from watson.analyzer import WatsonAnalyzer
from watson.config import APP_SOURCE_NAME, DEFAULT_LEAGUE_ID, LEAGUE_ID, LOCAL_MODE
from watson.league_client import LeagueClient


def initialize_watson():
    """Initialize Watson with the configured data source."""
    league_id = LEAGUE_ID or DEFAULT_LEAGUE_ID
    client = LeagueClient(league_id=league_id, source_name=APP_SOURCE_NAME, local_mode=LOCAL_MODE)
    watson = WatsonAnalyzer(client)
    return watson


def main():
    """Main Watson application entry point"""
    try:
        watson = initialize_watson()
        print("✓ Watson initialized and ready!")
        print(f"✓ Data source: {APP_SOURCE_NAME}")
        print(f"✓ League ID: {watson.client.league_id}")
        return watson
    except ValueError as e:
        print(f"✗ Initialization error: {e}")
        return None


if __name__ == "__main__":
    watson = main()
