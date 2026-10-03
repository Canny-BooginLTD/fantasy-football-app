"""Tests for ESPN historical ingestion helpers."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from watson.history_store import HistoricalDataStore
from watson.ingest import ingest_espn_history


class _FakeTeam:
    def __init__(self, team_name="Team One", wins=10, losses=4, points_for=1250):
        self.team_id = 1
        self.team_name = team_name
        self.wins = wins
        self.losses = losses
        self.points_for = points_for


class _FakeGameSide:
    def __init__(self, team_name):
        self.team_name = team_name


class _FakeGame:
    def __init__(self):
        self.home_team = _FakeGameSide("Home Team")
        self.away_team = _FakeGameSide("Away Team")
        self.home_score = 120.5
        self.away_score = 110.3


class _FakePlayer:
    def __init__(self, player_id, name, position, points=0, projected_points=None, trade_value=None, status=None, injury_status=None):
        self.playerId = player_id
        self.name = name
        self.position = position
        self.points = points
        self.projected_points = projected_points
        self.trade_value = trade_value
        self.status = status
        self.injuryStatus = injury_status


class _FakeLeague:
    def standings(self):
        return [_FakeTeam()]

    def box_scores(self):
        return [_FakeGame()]

    def free_agents(self, size=10):
        return [_FakePlayer(201, "Waiver QB", "QB", points=19.2)]


class _MultiSeasonLeague:
    def standings(self):
        return [_FakeTeam("Team One")]

    def box_scores(self):
        return [_FakeGame()]

    def free_agents(self, size=10):
        return [_FakePlayer(201, "Waiver QB", "QB", points=19.2), _FakePlayer(202, "Waiver RB", "RB", points=14.1)]


class _RangeLeague:
    def standings(self):
        return [_FakeTeam("Range Team")]

    def box_scores(self):
        return [_FakeGame()]

    def free_agents(self, size=10):
        return [_FakePlayer(301, "Range QB", "QB", points=21.5)]


def test_historical_store_round_trip(tmp_path):
    store = HistoricalDataStore(storage_path=str(tmp_path / "history.json"))
    store.save_snapshot({"league_id": "123", "season": 2025, "source": "espn-api"})
    store.save_snapshot({"league_id": "123", "season": 2024, "source": "espn-api"})

    snapshots = store.load_all()
    assert len(snapshots) == 2
    assert store.latest()["season"] == 2024
    assert store.get_by_season(2025)[0]["season"] == 2025


@patch("watson.espn_scraper.League", return_value=_FakeLeague())
def test_ingest_espn_history_writes_snapshots(_mock_league, tmp_path):
    snapshots = ingest_espn_history("123", year=2025, storage_path=str(tmp_path / "history.json"))
    assert len(snapshots) == 1
    assert snapshots[0]["league_id"] == "123"
    assert snapshots[0]["source"] == "espn-api"
    assert snapshots[0]["standings"][0]["team_name"] == "Team One"
    assert snapshots[0]["matchups"][0]["home_team"] == "Home Team"
    assert snapshots[0]["available_players"][0]["points"] == 19.2
    assert Path(tmp_path / "history.json").exists()


@patch("watson.espn_scraper.HISTORICAL_START_YEAR", 2024)
@patch("watson.espn_scraper.HISTORICAL_END_YEAR", "2025")
@patch("watson.espn_scraper.League", return_value=_RangeLeague())
def test_ingest_espn_history_bulk_imports_full_range(_mock_league, tmp_path):
    snapshots = ingest_espn_history("123", storage_path=str(tmp_path / "history.json"))
    assert len(snapshots) == 2
    assert {snapshot["season"] for snapshot in snapshots} == {2024, 2025}
    store = HistoricalDataStore(storage_path=str(tmp_path / "history.json"))
    assert len(store.load_all()) == 2
    assert store.get_by_season(2024)
    assert store.get_by_season(2025)
