"""Tests for Watson analyzer module"""

from unittest.mock import Mock

import pytest

from watson.analyzer import WatsonAnalyzer


class TestWatsonAnalyzer:
    """Test suite for WatsonAnalyzer"""

    @pytest.fixture
    def mock_league_client(self):
        """Create a mock league client"""
        client = Mock()
        client.get_league_data.return_value = {
            "teams": [
                {
                    "id": 1,
                    "strength": "balanced",
                    "roster": [
                        {"player_id": 101, "name": "Sample QB", "position": "QB", "projected_points": 22.1, "trade_value": 18, "market_position": "starter"},
                        {"player_id": 102, "name": "Sample RB", "position": "RB", "projected_points": 16.4, "trade_value": 20, "market_position": "starter"},
                        {"player_id": 103, "name": "Sample WR", "position": "WR", "projected_points": 14.3, "trade_value": 17, "market_position": "starter"},
                    ],
                }
            ],
            "available_players": [
                {"player_id": 201, "name": "Waiver QB", "position": "QB", "projected_points": 19.2},
                {"player_id": 202, "name": "Waiver RB", "position": "RB", "projected_points": 13.8},
                {"player_id": 203, "name": "Waiver WR", "position": "WR", "projected_points": 12.7},
            ],
            "players": [
                {"player_id": 101, "name": "Sample QB", "position": "QB", "injury_status": "Healthy", "trade_value": 18, "market_position": "starter"},
                {"player_id": 102, "name": "Sample RB", "position": "RB", "injury_status": "Questionable", "trade_value": 20, "market_position": "starter"},
                {"player_id": 103, "name": "Sample WR", "position": "WR", "injury_status": "Out", "trade_value": 17, "market_position": "starter"},
            ],
        }
        return client

    @pytest.fixture
    def watson(self, mock_league_client):
        """Create Watson instance with mock client"""
        return WatsonAnalyzer(mock_league_client)

    def test_initialization(self, watson):
        """Test Watson initializes correctly"""
        assert watson is not None
        assert watson.league_data is None

    def test_trade_recommendations(self, watson):
        """Test trade recommendation generation"""
        recommendations = watson.trade_recommendations(team_id=1)
        assert recommendations is not None
        assert recommendations["team_id"] == 1
        assert "trades" in recommendations
        assert "rationale" in recommendations

    def test_lineup_optimization(self, watson):
        """Test lineup optimization"""
        optimization = watson.lineup_optimization(team_id=1)
        assert optimization is not None
        assert optimization["team_id"] == 1
        assert "suggested_lineup" in optimization
        assert optimization["expected_points"] > 0

    def test_waiver_wire_analysis(self, watson):
        """Test waiver wire analysis"""
        analysis = watson.waiver_wire_analysis()
        assert analysis is not None
        assert "top_pickups" in analysis
        assert len(analysis["top_pickups"]) == 3

    def test_injury_alerts(self, watson):
        """Test injury alert generation"""
        alerts = watson.injury_alerts()
        assert alerts is not None
        assert "injured_players" in alerts
        assert len(alerts["questionable"]) == 1

    def test_trade_value_assessment(self, watson):
        """Test trade value assessment"""
        assessment = watson.trade_value_assessment(player_id=100)
        assert assessment is not None
        assert assessment["player_id"] == 100

