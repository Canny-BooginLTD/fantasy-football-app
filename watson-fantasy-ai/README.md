# Watson - Fantasy Football AI Assistant

Watson is the fantasy-football intelligence subpackage intended to live inside the master `fantasy-football-app` project. ESPN is used only as an optional historical data ingestion source; the app itself reads from local cached/imported data so your friends can run it without live ESPN access.

## Project structure

```text
fantasy-football-app/
  watson/
  tests/
  docs/
  credentials
  requirements.txt
  setup.py
  README.md
  .gitignore
```

## Quick Start

### Installation

```bash
cd fantasy-football-app
pip install -r requirements.txt
```

### Master app layout first

Before collecting any data, keep this package under the master app root as described above.

### Configuration

The app runs with local defaults out of the box. Optional environment variables:

```env
WATSON_SOURCE_NAME=local
WATSON_DEFAULT_LEAGUE_ID=local-league
WATSON_LOCAL_MODE=true
LEAGUE_ID=your_optional_internal_league_id
```

If you want ESPN historical ingestion, put your login/session values in a file named `credentials` at the repo root.

### Historical ESPN ingestion

Historical ESPN data is imported with `espn-api` and stored in a TinyDB-backed local NoSQL file at `~/.watson/historical_data.json` by default. The runtime app does not require ESPN access once the data is cached.

To import **all historical seasons**, set a start year with `WATSON_HISTORICAL_START_YEAR` (defaults to `2000`) and optionally cap the range with `WATSON_HISTORICAL_END_YEAR`. If no end year is set, Watson imports through the current season year.

You can run a bulk import from the terminal after installing the package:

```bash
watson-ingest 2064790109
```

### Usage

```python
from watson.main import initialize_watson

watson = initialize_watson()

trades = watson.trade_recommendations(team_id=1)
lineup = watson.lineup_optimization(team_id=1)
waivers = watson.waiver_wire_analysis()
injuries = watson.injury_alerts()
trade_value = watson.trade_value_assessment(player_id=101)
```

### Run the app

```bash
python -m watson.main
```

### Import ESPN history

```python
from watson.ingest import ingest_espn_history

ingest_espn_history("123456", year=2025)
```

### Inspect stored history

```python
from watson.history_store import HistoricalDataStore

store = HistoricalDataStore()
print(store.load_all())
```

## Features

- Trade recommendations from a local model
- Lineup optimization based on seeded league data
- Waiver wire ranking
- Injury monitoring
- Player trade value assessment
- Optional historical ingestion from ESPN
- TinyDB-backed historical snapshot storage

## Architecture

- `watson/` contains the Watson subpackage used by the master app
- `watson/main.py` wires the Watson package together
- `watson/league_client.py` is the data adapter for league data
- `watson/analyzer.py` owns feature building and model inference
- `watson/ingest.py` handles optional ESPN historical ingestion
- `watson/history_store.py` stores cached snapshots locally in TinyDB
- `watson/master_project.py` coordinates full-history imports and exports
- `watson/export_contract.py` defines the stable payload for downstream use inside the master app
- `watson/config.py` stores runtime settings

## Master app integration

The main app should treat Watson as a subfolder package and call its public entrypoints directly from the monorepo root. Keep the Watson internals inside `watson/` and connect app-level bootstrap code at the repo root rather than splitting into separate repos.

## Testing

```bash
pytest tests/
```

## Documentation

See [docs/WATSON.rst](docs/WATSON.rst) and [docs/REPO_LAYOUT.md](docs/REPO_LAYOUT.md) for API-level details and the repo blueprint.

## License

MIT
