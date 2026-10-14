"""Regression coverage shared by the local bot and standalone deploy bundle."""

import asyncio
import importlib
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tinydb import Query
from watson_analysis import WatsonAnalysis
from watson_predictor import WatsonPredictor
from watson_result_scraper import WatsonResultScraper
import espn_update


class PredictionTrackingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.home_patch = patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)
        self.env_patch = patch.dict(os.environ, {
            "WATSON_ANALYSIS_PATH": str(self.home / ".watson" / "analysis.json"),
            "WATSON_SEASON": "2026",
        })
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.db_path = self.home / ".watson" / "historical_data.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.path_patch = patch.object(espn_update, "DB_PATH", self.db_path)
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.bot_module = importlib.import_module("watson_discord_bot")
        self.bot_module._last_result_sync_error = None
        self.matchups = [
            self.matchup(week, completed=week < 6) for week in range(1, 7)
        ]
        self.store(self.matchups)

    @staticmethod
    def matchup(week, completed=True, home_score=120, away_score=100):
        return {
            "week": week, "home_team": "Home", "away_team": "Away",
            "home_score": home_score, "away_score": away_score,
            "home_projection": 140, "away_projection": 110,
            "completed": completed,
        }

    def store(self, matchups):
        espn_update.store_season({
            "season": 2026, "current_week": 6, "matchups": matchups,
            "standings": [],
        })

    def save(self, week, season=2026, reverse=False):
        analysis = WatsonAnalysis()
        try:
            team1, team2 = ("Away", "Home") if reverse else ("Home", "Away")
            return analysis.save_prediction(
                f"{team1} vs {team2}", team1, team2, "Home",
                {"team1": {"probability": 60}, "team2": {"probability": 40}},
                {"team1": 120, "team2": 100}, season=season, week=week
            )
        finally:
            analysis.close()

    def sync(self):
        scraper = WatsonResultScraper()
        try:
            return scraper.sync_results(2026)
        finally:
            scraper.close()

    def test_week_six_catches_up_all_five_weeks_and_is_idempotent(self):
        for week in range(1, 7):
            self.save(week)
        self.save(5)  # Multiple saved predictions for one matchup must all grade.
        self.save(5, season=2025)
        self.assertEqual(self.sync()["newly_recorded"], 6)
        self.assertEqual(self.sync()["newly_recorded"], 0)
        analysis = WatsonAnalysis()
        try:
            accuracy = analysis.get_prediction_accuracy()
            self.assertEqual(accuracy["total_predictions"], 6)
            self.assertEqual(accuracy["accuracy"], 100)
            self.assertEqual(accuracy["saved_predictions"], 8)
            self.assertEqual(accuracy["pending_predictions"], 2)
        finally:
            analysis.close()

    def test_zero_scores_ties_and_reversed_team_order(self):
        self.store([self.matchup(1, home_score=0, away_score=0),
                    self.matchup(2, home_score=120, away_score=100)])
        self.save(1)
        reversed_id = self.save(2, reverse=True)
        self.assertEqual(self.sync()["newly_recorded"], 2)
        analysis = WatsonAnalysis()
        try:
            results = analysis.results.all()
            self.assertEqual(results[0]["actual_winner"], "TIE")
            reversed_result = analysis.results.get(Query().prediction_id == reversed_id)
            self.assertEqual(reversed_result["team1_score"], 100)
            self.assertEqual(reversed_result["team2_score"], 120)
            self.assertEqual(reversed_result["actual_winner"], "Home")
        finally:
            analysis.close()

    def test_legacy_prediction_requires_explicit_week_then_grades(self):
        prediction_id = self.save(None, season=None)
        summary = self.sync()
        self.assertEqual(summary["unscoped_predictions"], 1)
        self.assertEqual(summary["newly_recorded"], 0)
        scraper = WatsonResultScraper()
        try:
            with self.assertRaises(ValueError):
                scraper.link_prediction(prediction_id, 2026, 7)
            scraper.link_prediction(prediction_id, 2026, 5)
        finally:
            scraper.close()
        self.assertEqual(self.sync()["newly_recorded"], 1)
        self.assertEqual(self.sync()["newly_recorded"], 0)

    def test_partial_scores_without_finality_are_not_graded(self):
        matchup = self.matchup(1)
        del matchup["completed"]
        self.store([matchup, self.matchup(6, completed=False)])
        self.save(1)
        self.save(6)
        self.assertEqual(self.sync()["newly_recorded"], 0)

    def test_record_result_is_idempotent_and_missing_id_is_error(self):
        pred_id = self.save(1)
        analysis = WatsonAnalysis()
        try:
            analysis.record_result(pred_id, "Home", 120, 100)
            analysis.record_result(pred_id, "Home", 120, 100)
            self.assertEqual(len(analysis.results), 1)
            with self.assertRaises(ValueError):
                analysis.record_result("missing", "Home", 120, 100)
        finally:
            analysis.close()

    def test_current_prediction_selects_week_six_not_first_repeat_matchup(self):
        predictor = WatsonPredictor()
        try:
            predictor._find_team_name = lambda name: name
            predictor.get_team_stats = lambda name: {"avg_points_per_season": 100}
            predictor.sleeper_cache = {}
            prediction = predictor.predict_current("Away", "Home")
            self.assertEqual((prediction["season"], prediction["week"]), (2026, 6))
            self.assertEqual(prediction["team1"]["projection"], 110)
            self.assertEqual(prediction["team2"]["projection"], 140)
        finally:
            predictor.close()

    def test_fetch_marks_previous_weeks_final_but_not_live_week(self):
        game = SimpleNamespace(
            home_team=SimpleNamespace(team_name="Home"),
            away_team=SimpleNamespace(team_name="Away"),
            home_score=120, away_score=100,
        )
        league = SimpleNamespace(
            current_week=6, standings=lambda: [],
            box_scores=lambda week: [game],
        )
        with patch.object(espn_update, "League", return_value=league):
            snapshot = espn_update.fetch_season(2026)
        self.assertEqual(snapshot["current_week"], 6)
        self.assertEqual([m["completed"] for m in snapshot["matchups"]],
                         [True, True, True, True, True, False])

    def test_manual_sync_refreshes_espn_on_any_day_and_grades_backlog(self):
        self.save(5)
        snapshot = {"season": 2026, "current_week": 6,
                    "standings": [], "matchups": self.matchups}
        ctx = SimpleNamespace(send=AsyncMock())
        with patch.object(self.bot_module, "fetch_season", return_value=snapshot) as fetch:
            asyncio.run(self.bot_module.sync_results.callback(ctx, 2026))
        fetch.assert_called_once_with(2026)
        embed = ctx.send.call_args.kwargs["embed"]
        self.assertIn("All Finalized Weeks", embed.description)
        self.assertEqual(embed.fields[1].value, "1 results")

    def test_multiweek_matchup_waits_for_entire_period_and_final_week_can_grade(self):
        game = SimpleNamespace(
            home_team=SimpleNamespace(team_name="Home"),
            away_team=SimpleNamespace(team_name="Away"),
            home_score=120, away_score=100,
        )
        league = SimpleNamespace(
            current_week=6, scoringPeriodId=6, standings=lambda: [],
            box_scores=lambda week: [game],
            settings=SimpleNamespace(matchup_periods={1: [5, 6]}),
        )
        with patch.object(espn_update, "League", return_value=league):
            snapshot = espn_update.fetch_season(2026)
        self.assertFalse(snapshot["matchups"][4]["completed"])
        self.assertFalse(snapshot["matchups"][5]["completed"])
        # ESPN can cap current_week at the final week even after the season ends.
        league.scoringPeriodId = 7
        with patch.object(espn_update, "League", return_value=league):
            snapshot = espn_update.fetch_season(2026)
        self.assertTrue(snapshot["matchups"][4]["completed"])
        self.assertTrue(snapshot["matchups"][5]["completed"])

    def test_accuracy_displays_saved_pending_instead_of_claiming_no_predictions(self):
        self.save(6)
        ctx = SimpleNamespace(send=AsyncMock())
        asyncio.run(self.bot_module.prediction_accuracy.callback(ctx))
        embed = ctx.send.call_args.kwargs["embed"]
        self.assertEqual(embed.fields[0].value, "1 saved / 1 pending")
        self.assertEqual(embed.fields[1].name, "No Graded Results")

    def test_automatic_sync_runs_on_startup_and_recovers_after_failure(self):
        ctx_bot = self.bot_module
        with patch.object(ctx_bot.bot, "change_presence", new=AsyncMock()), \
                patch.object(ctx_bot.automatic_result_sync, "is_running", return_value=False), \
                patch.object(ctx_bot.automatic_result_sync, "start") as start:
            asyncio.run(ctx_bot.on_ready())
        start.assert_called_once()
        with patch.object(ctx_bot.automatic_result_sync, "is_running", return_value=True), \
                patch.object(ctx_bot.automatic_result_sync, "start") as start, \
                patch.object(ctx_bot.bot, "change_presence", new=AsyncMock()):
            asyncio.run(ctx_bot.on_ready())
        start.assert_not_called()
        refresh = AsyncMock(side_effect=RuntimeError("ESPN unavailable"))
        with patch.object(ctx_bot, "_refresh_and_grade", refresh), self.assertLogs(level="ERROR"):
            asyncio.run(ctx_bot.automatic_result_sync())
        self.assertIn("ESPN unavailable", ctx_bot._last_result_sync_error)
        with patch.object(ctx_bot, "_refresh_and_grade",
                          AsyncMock(return_value={"unscoped_predictions": 0})):
            asyncio.run(ctx_bot.automatic_result_sync())
        self.assertIsNone(ctx_bot._last_result_sync_error)

    def test_configured_analysis_path_is_used(self):
        location = self.home / "persistent" / "analysis.json"
        with patch.dict(os.environ, {"WATSON_ANALYSIS_PATH": str(location)}):
            self.save(1)
            self.assertTrue(location.exists())

    def test_all_prediction_commands_save_season_and_week(self):
        for command in ("predict_current", "save_prediction", "all_odds"):
            ctx = SimpleNamespace(send=AsyncMock(), author=SimpleNamespace(id=123))
            with patch.object(WatsonPredictor, "_find_team_name", side_effect=lambda name: name), \
                    patch.object(WatsonPredictor, "get_team_stats",
                                 return_value={"avg_points_per_season": 100}):
                callback = getattr(self.bot_module, command).callback
                if command == "all_odds":
                    asyncio.run(callback(ctx))
                else:
                    asyncio.run(callback(ctx, teams="Home vs Away"))
        analysis = WatsonAnalysis()
        try:
            self.assertEqual(len(analysis.predictions), 3)
            self.assertTrue(all(p["season"] == 2026 and p["week"] == 6
                                for p in analysis.predictions.all()))
        finally:
            analysis.close()


if __name__ == "__main__":
    unittest.main()
