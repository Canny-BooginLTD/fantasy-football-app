# Watson Bot — Deploy Bundle (Wispbyte)

Self-contained Discord bot. Upload this folder only.

## Setup
- Start command: `python watson_discord_bot.py`
- Set **environment variables** in the host panel (do NOT upload a .env):
  - `DISCORD_TOKEN` — bot token (required)
  - `ESPN_S2`, `SWID` — ESPN cookies (required for `!sync` live scores)
  - `LEAGUE_ID` — defaults to 2064790109
  - `WATSON_SEASON` — optional season override (normally inferred from the date)
  - `WATSON_ANALYSIS_PATH` — optional absolute path to `analysis.json` on a
    host-provided persistent volume

## Data
- `data/historical_data.json` (6 years of league history) is auto-copied to
  `~/.watson/` on first run. Predictions/cache files are created there too.
- `~/.watson/` on free hosts may be wiped on redeploy. Back up
  `~/.watson/analysis.json` before uploading/restarting the bundle.
  For durable tracking, configure `WATSON_ANALYSIS_PATH` on a persistent
  volume and copy the existing file there **before** starting the bot.
  Merely changing the path does not migrate data or make host storage durable.
  League history re-seeds from the bundle; saved predictions cannot be recreated.

## Prediction tracking
- `!predict_current`, `!all_odds`, and `!save_prediction` save predictions with
  their season and week. Historical-only hypothetical matchups are unscoped
  and are not automatically graded.
- On connection/startup and every six hours, the bot refreshes ESPN scores
  and grades all finalized weeks, including missed weeks after downtime.
  At week 6, this catches up weeks 1–5. The current scoring week is not graded
  until ESPN advances to the next week; multiweek playoff matchups wait for
  the entire matchup period to end. Nonzero live scores are not final.
  ESPN access/cookies must be valid. Failures appear in host logs and
  `!prediction_accuracy`.
- `!sync_results [season]` refreshes ESPN and performs the same catch-up on
  **any day**, without duplicating recorded results.
- Older predictions have no saved season/week. Run `!backfill_predictions` to
  auto-link them (unique matchups directly; repeat matchups by timestamp) and
  grade in one step. Anything it reports as ambiguous: `!pending_predictions [page]`
  to find IDs, then `!link_prediction "<prediction_id>" 2026 5` (substitute the
  actual season/week), then `!sync_results 2026`. Quote IDs containing spaces.
  Team names alone are not safe for backfilling repeat matchups.
- `!prediction_accuracy` distinguishes saved/pending predictions from graded
  results. It cannot report historical prediction accuracy for weeks with no
  saved predictions; do not create predictions after seeing the results.

## Size
~200 KB of code/data; deps (~60 MB installed) fit well under 512 MB RAM / 1 GB disk.
