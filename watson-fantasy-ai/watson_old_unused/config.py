"""Configuration for Watson"""

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = ROOT_DIR / "credentials"
DOTENV_FILE = ROOT_DIR / ".env"

if CREDENTIALS_FILE.exists():
    load_dotenv(CREDENTIALS_FILE)
load_dotenv(DOTENV_FILE)

APP_SOURCE_NAME = os.getenv("WATSON_SOURCE_NAME", "local")
DEFAULT_LEAGUE_ID = os.getenv("WATSON_DEFAULT_LEAGUE_ID", "local-league")
LEAGUE_ID = os.getenv("LEAGUE_ID")
LOCAL_MODE = os.getenv("WATSON_LOCAL_MODE", "true").lower() in {"1", "true", "yes", "on"}
ESPN_USERNAME = os.getenv("ESPN_USERNAME")
ESPN_PASSWORD = os.getenv("ESPN_PASSWORD")
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")
HISTORICAL_START_YEAR = int(os.getenv("WATSON_HISTORICAL_START_YEAR", "2000"))
HISTORICAL_END_YEAR = os.getenv("WATSON_HISTORICAL_END_YEAR")
DESKTOP_PATH = os.path.expanduser("~/Desktop")
