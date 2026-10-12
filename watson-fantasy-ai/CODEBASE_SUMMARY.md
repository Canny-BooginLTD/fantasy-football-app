# Watson Fantasy Football Bot - Clean Codebase

## Core Files (Production)

### Main Bot
- **watson_discord_bot.py** (36 KB)
  - Discord bot with 19 commands
  - Auto-saves all predictions
  - Case-insensitive team aliases/abbreviations
  - Vegas moneyline odds display

### Predictors & Analysis
- **watson_predictor.py** (13 KB)
  - Prediction engine: 80% current projections + 20% historical
  - Vegas moneyline odds calculation
  - Season winner predictions
  - Head-to-head history

- **watson_query.py** (3.2 KB)
  - Database queries for historical league data
  - Standings, matchups, team stats

- **watson_analysis.py** (8.5 KB)
  - Prediction tracking and accuracy analysis
  - Confidence-level breakdown
  - Improvement recommendations

- **watson_result_scraper.py** (4.4 KB)
  - Auto-scrape completed matchups
  - Compare predictions vs actual results
  - Grade predictions

### Data Sources
- **sleeper_scraper.py** (5.6 KB)
  - Weekly Sleeper API sync (projections + stats)
  - Local caching to avoid API hammering
  - Converts player projections to team totals

### Team Management
- **team_abbrev.py** (7 KB)
  - Team abbreviations (VG, SF, MVDT, TCR, etc.)
  - Player/owner first-name aliases
  - Case-insensitive team resolution
  - Supports 50+ teams across 2021-2026

### Utilities
- **setup.py** (1 KB)
  - Package metadata

## Archived (Old)
- **watson_old_unused/** - Legacy analyzer/ingest modules (not used)

## Configuration Files
- **.env** - Discord token, Sleeper league ID
- **.gitignore** - Prevents credentials from being committed
- **requirements.txt** - Python dependencies

## Data Storage
- **~/.watson/sleeper_cache.json** - Weekly Sleeper projections cache
- **~/.watson/analysis.json** - Prediction tracking database
- **~/.watson/historical_data.json** - 6 years of league history

## Summary
- **Total Lines**: ~2,000 (core files only)
- **Commands**: 19 fully-tested Discord commands
- **No Duplicates**: Consolidated all view/show scripts
- **Clean Imports**: All dependencies used
- **Ready for Deployment**: All old code archived

