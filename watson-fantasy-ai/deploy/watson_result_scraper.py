#!/usr/bin/env python3
"""Watson Result Scraper - Auto-record completed matchup results"""

from watson_query import WatsonLeagueDB
from watson_analysis import WatsonAnalysis
from typing import List, Dict, Any
from datetime import datetime

class WatsonResultScraper:
    """Automatically scrape and record completed matchup results"""

    def __init__(self):
        self.db = WatsonLeagueDB()
        self.analysis = WatsonAnalysis()

    def get_completed_matchups(self, season: int) -> List[Dict[str, Any]]:
        """Get all completed matchups for a season"""
        matchups = self.db.get_matchups(season)
        completed = []

        for matchup in matchups:
            # Matchup is completed if both teams have scores > 0
            if matchup.get('home_score', 0) > 0 and matchup.get('away_score', 0) > 0:
                completed.append(matchup)

        return completed

    def find_prediction_for_matchup(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """Find a saved prediction matching this matchup"""
        predictions = self.analysis.predictions.all()

        for pred in predictions:
            # Check if prediction matches this matchup
            matchup_str = pred.get('matchup', '').lower()
            home_lower = home_team.lower()
            away_lower = away_team.lower()

            if (home_lower in matchup_str and away_lower in matchup_str) or \
               (away_lower in matchup_str and home_lower in matchup_str):
                return pred

        return None

    def sync_results(self, season: int) -> Dict[str, Any]:
        """Scan completed matchups and record results for ungraded predictions"""
        completed_matchups = self.get_completed_matchups(season)

        summary = {
            "season": season,
            "processed": 0,
            "already_graded": 0,
            "newly_recorded": 0,
            "no_prediction_found": 0,
            "results": []
        }

        for matchup in completed_matchups:
            home_team = matchup['home_team']
            away_team = matchup['away_team']
            home_score = matchup['home_score']
            away_score = matchup['away_score']

            # Determine actual winner
            actual_winner = home_team if home_score > away_score else away_team

            # Find prediction for this matchup
            prediction = self.find_prediction_for_matchup(home_team, away_team)

            summary["processed"] += 1

            if not prediction:
                summary["no_prediction_found"] += 1
                continue

            pred_id = prediction.get('id')
            pred_status = prediction.get('status', 'pending')

            # Check if already recorded
            if pred_status == 'completed':
                summary["already_graded"] += 1
                continue

            # Record the result
            self.analysis.record_result(
                pred_id,
                actual_winner,
                home_score,
                away_score
            )

            summary["newly_recorded"] += 1
            summary["results"].append({
                "prediction_id": pred_id,
                "matchup": f"{home_team} vs {away_team}",
                "predicted_winner": prediction.get('predicted_winner'),
                "actual_winner": actual_winner,
                "correct": prediction.get('predicted_winner') == actual_winner,
                "scores": f"{home_score} - {away_score}"
            })

        return summary

    def close(self):
        self.db.close()
        self.analysis.close()


if __name__ == "__main__":
    scraper = WatsonResultScraper()

    print("\n" + "="*80)
    print("WATSON RESULT SCRAPER")
    print("="*80 + "\n")

    current_season = 2026
    summary = scraper.sync_results(current_season)

    print(f"Season {summary['season']} Sync Results:")
    print(f"  Processed: {summary['processed']} matchups")
    print(f"  Already Graded: {summary['already_graded']}")
    print(f"  Newly Recorded: {summary['newly_recorded']}")
    print(f"  No Prediction Found: {summary['no_prediction_found']}")

    if summary['results']:
        print(f"\nNewly Recorded Results:")
        for result in summary['results']:
            status = "✅ CORRECT" if result['correct'] else "❌ WRONG"
            print(f"  {status} - {result['matchup']}")
            print(f"    Predicted: {result['predicted_winner']}, Actual: {result['actual_winner']}, Score: {result['scores']}")

    scraper.close()

