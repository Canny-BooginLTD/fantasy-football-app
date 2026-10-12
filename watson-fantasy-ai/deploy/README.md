# Watson Bot — Deploy Bundle (Wispbyte)

Self-contained Discord bot. Upload this folder only.

## Setup
- Start command: `python watson_discord_bot.py`
- Set **environment variables** in the host panel (do NOT upload a .env):
  - `DISCORD_TOKEN` — bot token (required)
  - `ESPN_S2`, `SWID` — ESPN cookies (required for `!sync` live scores)
  - `LEAGUE_ID` — defaults to 2064790109

## Data
- `data/historical_data.json` (6 years of league history) is auto-copied to
  `~/.watson/` on first run. Predictions/cache files are created there too.
- Note: `~/.watson/` on free hosts may be wiped on redeploy; prediction
  tracking (`analysis.json`) is not persistent. League history re-seeds
  from the bundle, and `!sync` refreshes live scores from ESPN.

## Size
~200 KB of code/data; deps (~60 MB installed) fit well under 512 MB RAM / 1 GB disk.
