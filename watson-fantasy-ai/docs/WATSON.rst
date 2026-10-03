Watson - Fantasy Football AI Assistant
=======================================

Overview
--------
Watson is a local-first fantasy football assistant built around an in-house model pipeline.
ESPN is used only as an optional historical ingestion source. The runtime app reads from
local cached or imported data so it can run without live ESPN access.

Features
--------

**Trade Intelligence**
- Trade recommendations based on local league features
- Trade value assessment for fair offers
- Trade trend analysis across league

**Lineup Optimization**
- Optimal starting lineup suggestions
- Injury and bye week impact analysis
- Strength-of-schedule recommendations

**Waiver Wire Analysis**
- Available player rankings
- Pickup priority by position
- Trending player identification

**Player Monitoring**
- Injury alerts
- Performance trending
- Trade deadline notifications

**Historical Storage**
- TinyDB-backed NoSQL snapshot storage
- Season-level lookup for imported ESPN data
- Bulk ingestion and append-only writes

Setup
-----

1. Install dependencies::

    pip install -r requirements.txt

2. Configure optional environment variables::

    WATSON_SOURCE_NAME=local
    WATSON_DEFAULT_LEAGUE_ID=local-league
    WATSON_LOCAL_MODE=true

   Or place your ESPN login/session values in a `credentials` file at the repo root before importing historical data.

3. Run Watson::

    python -m watson.main

4. Optionally import historical ESPN data::

    from watson.ingest import ingest_espn_history
    ingest_espn_history("123456", year=2025)

API Reference
-------------

**WatsonAnalyzer.trade_recommendations(team_id)**
    Returns suggested trades with rationale

**WatsonAnalyzer.lineup_optimization(team_id)**
    Returns an optimized starting lineup and expected points

**WatsonAnalyzer.waiver_wire_analysis()**
    Returns ranked list of available players

**WatsonAnalyzer.injury_alerts()**
    Returns players with injury concerns

**WatsonAnalyzer.trade_value_assessment(player_id)**
    Evaluates trade value of a specific player

**ingest_espn_history(league_id, year=None, storage_path=None)**
    Scrapes historical ESPN data and stores normalized snapshots locally

**HistoricalDataStore.load_all()**
    Returns all stored historical snapshots

**HistoricalDataStore.get_by_season(season)**
    Returns snapshots for a specific season

Architecture
------------

``league_client.py``
    Data adapter for league snapshots and seeded local data

``analyzer.py``
    AI analysis engine for feature building and model inference

``ingest.py``
    Optional ESPN historical ingestion entrypoint

``espn_scraper.py``
    ESPN historical adapter powered by `espn-api`

``history_store.py``
    TinyDB-backed local persistence for imported historical snapshots

``config.py``
    Runtime configuration and environment variable management

``main.py``
    Application entry point and initialization

Development
-----------

Run tests::

    pytest tests/

Test individual modules::

    python -m pytest tests/test_analyzer.py -v
    python -m pytest tests/test_ingest.py -v
