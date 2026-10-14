#!/usr/bin/env python3
"""Grade saved predictions against finalized ESPN matchups."""

from watson_query import WatsonLeagueDB
from watson_analysis import WatsonAnalysis
from tinydb import Query
from typing import List, Dict, Any
from datetime import datetime


class WatsonResultScraper:
    def __init__(self):
        self.db = WatsonLeagueDB()
        self.analysis = WatsonAnalysis()

    def get_completed_matchups(self, season: int) -> List[Dict[str, Any]]:
        return [
            matchup for matchup in self.db.get_matchups(season)
            if matchup.get("completed") is True
            and matchup.get("home_team") and matchup.get("away_team")
            and isinstance(matchup.get("home_score"), (int, float))
            and isinstance(matchup.get("away_score"), (int, float))
        ]

    @staticmethod
    def _teams_match(prediction, matchup):
        return {prediction["team1"].casefold(), prediction["team2"].casefold()} == {
            matchup["home_team"].casefold(), matchup["away_team"].casefold()
        }

    def link_prediction(self, prediction_id: str, season: int, week: int):
        """Explicitly scope an older prediction whose week was never saved."""
        pred = self.analysis.predictions.get(Query().id == prediction_id)
        if not pred:
            raise ValueError(f"Prediction {prediction_id} not found")
        if pred["status"] != "pending":
            raise ValueError("Only pending predictions can be linked")
        candidates = [
            m for m in self.db.get_matchups(season)
            if m.get("week") == week and self._teams_match(pred, m)
        ]
        if len(candidates) != 1:
            raise ValueError("No unique ESPN matchup for these teams in that season/week. Run !sync first.")
        self.analysis.predictions.update(
            {"season": season, "week": week}, Query().id == prediction_id
        )

    def backfill_predictions(self, season: int) -> Dict[str, Any]:
        """Bulk-link unscoped pending predictions to season/week automatically.

        A prediction whose team pair plays only one week that season links
        directly. Repeat matchups are resolved by comparing the prediction's
        timestamp against already-scoped predictions (7-day week spacing);
        anything still ambiguous is left for !link_prediction.
        """
        summary = {"season": season, "linked": 0, "ambiguous": [], "no_schedule_match": []}
        matchups = self.db.get_matchups(season)

        def candidate_weeks(pred):
            return sorted({
                m["week"] for m in matchups
                if m.get("week") is not None and self._teams_match(pred, m)
            })

        predictions = self.analysis.predictions.all()
        unscoped = [
            p for p in predictions
            if p.get("status") == "pending"
            and (p.get("season") is None or p.get("week") is None)
        ]
        # Timestamp anchors from predictions whose week is known
        anchors = [
            (datetime.fromisoformat(p["timestamp"]), p["week"])
            for p in predictions
            if p.get("season") == season and p.get("week") is not None and p.get("timestamp")
        ]

        def link(pred, week):
            self.analysis.predictions.update(
                {"season": season, "week": week}, Query().id == pred["id"]
            )
            anchors.append((datetime.fromisoformat(pred["timestamp"]), week))
            summary["linked"] += 1

        # Unique schedule matches first; they also become timestamp anchors.
        deferred = []
        for pred in unscoped:
            weeks = candidate_weeks(pred)
            if len(weeks) == 1:
                link(pred, weeks[0])
            elif not weeks:
                summary["no_schedule_match"].append(pred["id"])
            else:
                deferred.append((pred, weeks))

        for pred, weeks in deferred:
            ts = datetime.fromisoformat(pred["timestamp"])
            inferred = {
                anchor_week + round((ts - anchor_ts).days / 7)
                for anchor_ts, anchor_week in anchors
            }
            matched = inferred & set(weeks)
            if len(matched) == 1:
                link(pred, matched.pop())
            else:
                summary["ambiguous"].append(pred["id"])
        return summary

    def sync_results(self, season: int) -> Dict[str, Any]:
        """Catch up every finalized week, grading each scoped prediction once."""
        summary = {
            "season": season, "processed": 0, "already_graded": 0,
            "newly_recorded": 0, "no_prediction_found": 0,
            "unscoped_predictions": 0, "results": []
        }
        predictions = self.analysis.predictions.all()
        summary["unscoped_predictions"] = sum(
            p.get("status") == "pending" and
            (p.get("season") is None or p.get("week") is None)
            for p in predictions
        )
        for matchup in self.get_completed_matchups(season):
            summary["processed"] += 1
            matches = [
                p for p in predictions
                if p.get("season") == season and p.get("week") == matchup.get("week")
                and self._teams_match(p, matchup)
            ]
            if not matches:
                summary["no_prediction_found"] += 1
            for prediction in matches:
                if prediction.get("status") == "completed":
                    summary["already_graded"] += 1
                    continue
                home_score, away_score = matchup["home_score"], matchup["away_score"]
                actual_winner = (
                    "TIE" if home_score == away_score else
                    matchup["home_team"] if home_score > away_score else matchup["away_team"]
                )
                home_first = prediction["team1"].casefold() == matchup["home_team"].casefold()
                self.analysis.record_result(
                    prediction["id"], actual_winner,
                    home_score if home_first else away_score,
                    away_score if home_first else home_score
                )
                summary["newly_recorded"] += 1
                summary["results"].append({
                    "prediction_id": prediction["id"],
                    "matchup": f"Week {matchup['week']}: {prediction['matchup']}",
                    "predicted_winner": prediction["predicted_winner"],
                    "actual_winner": actual_winner,
                    "correct": prediction["predicted_winner"] == actual_winner,
                    "scores": f"{home_score} - {away_score}"
                })
        return summary

    def close(self):
        self.db.close()
        self.analysis.close()


if __name__ == "__main__":
    import argparse
    import json
    from datetime import datetime
    from espn_update import update_season

    parser = argparse.ArgumentParser(description="Refresh ESPN and grade finalized predictions")
    parser.add_argument("season", type=int, nargs="?", default=datetime.now().year)
    season = parser.parse_args().season
    update_season(season)
    scraper = WatsonResultScraper()
    try:
        print(json.dumps(scraper.sync_results(season), indent=2))
    finally:
        scraper.close()
