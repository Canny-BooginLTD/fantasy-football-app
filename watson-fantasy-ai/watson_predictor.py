#!/usr/bin/env python3
"""Watson Fantasy Football Predictions Engine"""

from watson_query import WatsonLeagueDB
from typing import Dict, List, Any
import json
from pathlib import Path

class WatsonPredictor:
    """Analyze historical data and make predictions"""

    def __init__(self):
        self.db = WatsonLeagueDB()
        self.seasons = self.db.get_seasons()
        self.sleeper_cache = self._load_sleeper_cache()

    def _load_sleeper_cache(self) -> Dict[str, Any]:
        """Load cached Sleeper projections"""
        cache_file = Path.home() / ".watson" / "sleeper_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _find_team_name(self, team_input: str) -> str:
        """Find the actual team name in the database with robust normalization"""
        def normalize(s: str) -> str:
            """Normalize team names: lowercase, strip punctuation/spacing variance"""
            if not s:
                return ""
            s = s.lower()
            # Normalize apostrophes
            s = s.replace("'", "'").replace("`", "'").replace("'", "'")
            # Keep alphanumeric, spaces, and hyphens only
            cleaned = []
            for ch in s:
                if ch.isalnum() or ch.isspace() or ch == '-':
                    cleaned.append(ch)
            return " ".join("".join(cleaned).split())

        found_teams = set()
        for season in self.seasons:
            standings = self.db.get_standings(season, limit=100)
            for team in standings:
                found_teams.add(team['team_name'])

        target = normalize(team_input)

        # 1) Exact normalized match
        for db_team in found_teams:
            if normalize(db_team) == target:
                return db_team

        # 2) Partial/token match fallback
        target_tokens = set(target.split())
        for db_team in found_teams:
            db_norm = normalize(db_team)
            db_tokens = set(db_norm.split())
            if target and (target in db_norm or target_tokens.issubset(db_tokens)):
                return db_team

        return None

    def get_team_stats(self, team_name: str) -> Dict[str, Any]:
        """Get all-time stats for a team across all seasons"""
        total_wins = 0
        total_losses = 0
        total_points = 0
        total_matchups = 0

        # Find the matched team name
        matched_team = self._find_team_name(team_name)
        if not matched_team:
            return {
                "team_name": team_name,
                "total_wins": 0,
                "total_losses": 0,
                "total_points": 0,
                "avg_points_per_season": 0,
                "win_rate": 0,
                "seasons_played": 0
            }

        for season in self.seasons:
            standings = self.db.get_standings(season, limit=100)
            for team in standings:
                if team['team_name'] == matched_team:
                    total_wins += team['wins']
                    total_losses += team['losses']
                    total_points += team['points_for']
                    total_matchups += 1

        if total_matchups > 0:
            avg_points = total_points / total_matchups
            win_rate = total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0
        else:
            avg_points = 0
            win_rate = 0

        return {
            "team_name": matched_team,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "total_points": total_points,
            "avg_points_per_season": avg_points,
            "win_rate": win_rate,
            "seasons_played": total_matchups
        }

    def predict_matchup_current(self, team1: str, team2: str) -> Dict[str, Any]:
        """Predict CURRENT matchup: 80% player projections + 20% historical
        Falls back to historical-only if no current matchup exists"""
        actual_team1 = self._find_team_name(team1)
        actual_team2 = self._find_team_name(team2)

        if not actual_team1 or not actual_team2:
            return {"error": "Team not found"}

        current_season = max(self.seasons)
        matchups = self.db.get_matchups(current_season)

        current_matchup = None
        for matchup in matchups:
            if (matchup['home_team'] == actual_team1 and matchup['away_team'] == actual_team2) or \
               (matchup['home_team'] == actual_team2 and matchup['away_team'] == actual_team1):
                current_matchup = matchup
                break

        # If no current matchup exists, fall back to historical prediction
        if not current_matchup:
            return self.predict_matchup_historical_only(actual_team1, actual_team2)

        # Get projections from Sleeper cache (80% weight)
        proj1 = current_matchup.get('home_projection', 0)
        proj2 = current_matchup.get('away_projection', 0)

        # Try to load from Sleeper cache if ESPN projections are zero
        if (proj1 == 0 or proj2 == 0) and self.sleeper_cache:
            # Find current week matchups in cache
            for week_key in self.sleeper_cache:
                if week_key.startswith('week_') and week_key.endswith('_matchups'):
                    cached_matchups = self.sleeper_cache.get(week_key, [])
                    for cached_m in cached_matchups:
                        # Try to match by roster IDs or team names
                        if current_matchup['home_team'] == actual_team1:
                            if proj1 == 0:
                                proj1 = cached_m.get('home_projection', proj1)
                            if proj2 == 0:
                                proj2 = cached_m.get('away_projection', proj2)

        # Get historical (20% weight)
        hist1 = self.get_team_stats(actual_team1)['avg_points_per_season']
        hist2 = self.get_team_stats(actual_team2)['avg_points_per_season']

        # Calculate: 80% current + 20% historical
        score1 = (proj1 * 0.8) + (hist1 * 0.2)
        score2 = (proj2 * 0.8) + (hist2 * 0.2)

        # Calculate implied probability
        if score1 + score2 > 0:
            prob1 = score1 / (score1 + score2)
            prob2 = score2 / (score1 + score2)
        else:
            prob1 = prob2 = 0.5

        # Convert to Vegas moneyline odds
        def prob_to_moneyline(prob):
            """Convert probability to American moneyline odds"""
            if prob >= 0.5:
                return round(-100 / (1/prob - 1))
            else:
                return round(100 * (1/prob - 1))

        ml1 = prob_to_moneyline(prob1)
        ml2 = prob_to_moneyline(prob2)

        if score1 > score2:
            winner = actual_team1
        elif score2 > score1:
            winner = actual_team2
        else:
            winner = "TIE"

        return {
            "matchup": f"{actual_team1} vs {actual_team2}",
            "predicted_winner": winner,
            "implied_probability_pct": round(max(prob1, prob2) * 100, 1),
            "moneyline_odds": {
                "team1": {
                    "name": actual_team1,
                    "odds": ml1,
                    "probability": round(prob1 * 100, 1),
                },
                "team2": {
                    "name": actual_team2,
                    "odds": ml2,
                    "probability": round(prob2 * 100, 1),
                }
            },
            "team1": {
                "name": actual_team1,
                "projection": round(proj1, 2),
                "historical_avg": round(hist1, 2),
                "weighted_score": round(score1, 2),
            },
            "team2": {
                "name": actual_team2,
                "projection": round(proj2, 2),
                "historical_avg": round(hist2, 2),
                "weighted_score": round(score2, 2),
            }
        }

    def predict_matchup_historical_only(self, team1: str, team2: str) -> Dict[str, Any]:
        """Predict matchup using ONLY historical data (used for non-existent matchups)"""
        actual_team1 = self._find_team_name(team1)
        actual_team2 = self._find_team_name(team2)

        if not actual_team1 or not actual_team2:
            return {"error": "Team not found"}

        stats1 = self.get_team_stats(actual_team1)
        stats2 = self.get_team_stats(actual_team2)

        avg1 = stats1['avg_points_per_season']
        avg2 = stats2['avg_points_per_season']

        # Calculate implied probability from historical averages
        if avg1 + avg2 > 0:
            prob1 = avg1 / (avg1 + avg2)
            prob2 = avg2 / (avg1 + avg2)
        else:
            prob1 = prob2 = 0.5

        # Convert to Vegas moneyline odds
        def prob_to_moneyline(prob):
            if prob >= 0.5:
                return round(-100 / (1/prob - 1))
            else:
                return round(100 * (1/prob - 1))

        ml1 = prob_to_moneyline(prob1)
        ml2 = prob_to_moneyline(prob2)

        if avg1 > avg2:
            winner = actual_team1
        elif avg2 > avg1:
            winner = actual_team2
        else:
            winner = "TIE"

        return {
            "matchup": f"{actual_team1} vs {actual_team2}",
            "predicted_winner": winner,
            "implied_probability_pct": round(max(prob1, prob2) * 100, 1),
            "prediction_type": "HISTORICAL ONLY (no current week matchup)",
            "moneyline_odds": {
                "team1": {
                    "name": actual_team1,
                    "odds": ml1,
                    "probability": round(prob1 * 100, 1),
                },
                "team2": {
                    "name": actual_team2,
                    "odds": ml2,
                    "probability": round(prob2 * 100, 1),
                }
            },
            "team1": {
                "name": actual_team1,
                "projection": 0,
                "historical_avg": round(avg1, 2),
                "weighted_score": round(avg1, 2),
            },
            "team2": {
                "name": actual_team2,
                "projection": 0,
                "historical_avg": round(avg2, 2),
                "weighted_score": round(avg2, 2),
            }
        }

    def predict_current(self, team1: str, team2: str) -> Dict[str, Any]:
        """Compatibility alias for bot command."""
        return self.predict_matchup_current(team1, team2)

    def predict_matchup(self, team1: str, team2: str) -> Dict[str, Any]:
        """Predict matchup using historical data only"""
        actual_team1 = self._find_team_name(team1)
        actual_team2 = self._find_team_name(team2)

        if not actual_team1 or not actual_team2:
            return {"error": "Team not found"}

        stats1 = self.get_team_stats(actual_team1)
        stats2 = self.get_team_stats(actual_team2)

        avg1 = stats1['avg_points_per_season']
        avg2 = stats2['avg_points_per_season']

        if avg1 > avg2:
            winner = actual_team1
            conf = min(100, ((avg1 - avg2) / max(avg1, avg2)) * 100)
        elif avg2 > avg1:
            winner = actual_team2
            conf = min(100, ((avg2 - avg1) / max(avg1, avg2)) * 100)
        else:
            winner = "TIE"
            conf = 50

        return {
            "matchup": f"{actual_team1} vs {actual_team2}",
            "predicted_winner": winner,
            "confidence": round(conf, 1),
            "team1_avg": round(avg1, 2),
            "team2_avg": round(avg2, 2),
            "team1_winrate": round(stats1['win_rate'] * 100, 1),
            "team2_winrate": round(stats2['win_rate'] * 100, 1)
        }

    def head_to_head(self, team1: str, team2: str) -> Dict[str, Any]:
        """Get head-to-head history"""
        actual_team1 = self._find_team_name(team1)
        actual_team2 = self._find_team_name(team2)

        if not actual_team1 or not actual_team2:
            return {"error": "Team not found"}

        h2h = []
        for season in self.seasons:
            for matchup in self.db.get_matchups(season):
                if (matchup['home_team'] == actual_team1 and matchup['away_team'] == actual_team2) or \
                   (matchup['home_team'] == actual_team2 and matchup['away_team'] == actual_team1):
                    h2h.append(matchup)

        team1_wins = sum(1 for m in h2h if (m['home_team'] == actual_team1 and m['home_score'] > m['away_score']) or \
                                           (m['away_team'] == actual_team1 and m['away_score'] > m['home_score']))

        return {
            "team1": actual_team1,
            "team2": actual_team2,
            "record": f"{team1_wins}-{len(h2h) - team1_wins}",
            "matchups": len(h2h)
        }

    def predict_season_winner(self, year: int = None) -> Dict[str, Any]:
        """Predict season winner based on historical performance and current projections"""
        if year is None:
            year = max(self.seasons)

        standings = self.db.get_standings(year, limit=100)

        predictions = []
        for team in standings:
            team_name = team['team_name']
            stats = self.get_team_stats(team_name)

            predictions.append({
                "team": team_name,
                "current_record": f"{team['wins']}-{team['losses']}",
                "current_points": round(team['points_for'], 2),
                "historical_avg": round(stats['avg_points_per_season'], 2),
                "win_probability": round(stats['win_rate'] * 100, 1),
                "total_historical_wins": stats['total_wins']
            })

        # Sort by win probability
        predictions.sort(key=lambda x: x['win_probability'], reverse=True)

        return {
            "year": year,
            "predictions": predictions,
            "top_3": predictions[:3] if len(predictions) >= 3 else predictions
        }

    def close(self):
        self.db.close()

