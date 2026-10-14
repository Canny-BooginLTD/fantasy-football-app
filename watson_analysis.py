#!/usr/bin/env python3
"""Watson Prediction Analysis & Learning System"""

from pathlib import Path
from tinydb import TinyDB, Query
from typing import Dict, List, Any
from datetime import datetime
import json
import os

class WatsonAnalysis:
    """Track prediction accuracy and improve models over time"""

    def __init__(self):
        self.db_path = Path(os.getenv("WATSON_ANALYSIS_PATH", str(Path.home() / ".watson" / "analysis.json"))).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = TinyDB(self.db_path)
        self.predictions = self.db.table("predictions")
        self.results = self.db.table("results")
        self.model_performance = self.db.table("model_performance")

    def save_prediction(self, matchup: str, team1: str, team2: str,
                       predicted_winner: str, odds: Dict[str, Any],
                       weighted_scores: Dict[str, float], season: int = None,
                       week: int = None) -> str:
        """Save a prediction before the matchup happens"""
        prediction_id = f"{matchup}_{datetime.now().isoformat()}"

        doc = {
            "id": prediction_id,
            "timestamp": datetime.now().isoformat(),
            "matchup": matchup,
            "team1": team1,
            "team2": team2,
            "season": season,
            "week": week,
            "predicted_winner": predicted_winner,
            "odds": odds,
            "weighted_scores": weighted_scores,
            "status": "pending"  # pending, completed, graded
        }

        self.predictions.insert(doc)
        print(f"✅ Saved prediction: {prediction_id}")
        return prediction_id

    def record_result(self, prediction_id: str, actual_winner: str,
                     team1_score: float, team2_score: float):
        """Record the actual result of a matchup"""
        Pred = Query()
        pred = self.predictions.get(Pred.id == prediction_id)

        if not pred:
            raise ValueError(f"Prediction {prediction_id} not found")

        if self.results.get(Query().prediction_id == prediction_id):
            return

        # Determine if prediction was correct
        correct = (pred['predicted_winner'] == actual_winner)

        result_doc = {
            "prediction_id": prediction_id,
            "timestamp": datetime.now().isoformat(),
            "actual_winner": actual_winner,
            "team1_score": team1_score,
            "team2_score": team2_score,
            "prediction_correct": correct,
            "confidence_in_prediction": pred['odds']['team1']['probability'] if pred['predicted_winner'] == pred['team1'] else pred['odds']['team2']['probability'],
        }

        self.results.insert(result_doc)

        # Update prediction status
        self.predictions.update({"status": "completed"}, Pred.id == prediction_id)

        status = "✅ CORRECT" if correct else "❌ WRONG"
        print(f"{status} - {pred['matchup']}: {actual_winner} won")

    def get_prediction_accuracy(self) -> Dict[str, Any]:
        """Calculate overall prediction accuracy"""
        all_results = self.results.all()

        if not all_results:
            return {"accuracy": 0, "correct": 0, "wrong": 0, "total_predictions": 0,
                    "saved_predictions": len(self.predictions),
                    "pending_predictions": len(self.predictions.search(Query().status == "pending"))}

        correct = sum(1 for r in all_results if r['prediction_correct'])
        total = len(all_results)
        accuracy = (correct / total) * 100 if total > 0 else 0

        return {
            "accuracy": round(accuracy, 1),
            "correct": correct,
            "total_predictions": total,
            "wrong": total - correct,
            "saved_predictions": len(self.predictions),
            "pending_predictions": len(self.predictions.search(Query().status == "pending"))
        }

    def get_prediction_by_confidence(self) -> Dict[str, Any]:
        """Analyze accuracy by confidence level"""
        all_results = self.results.all()

        # Group by confidence levels
        high_conf = [r for r in all_results if r['confidence_in_prediction'] >= 55]
        medium_conf = [r for r in all_results if 45 <= r['confidence_in_prediction'] < 55]
        low_conf = [r for r in all_results if r['confidence_in_prediction'] < 45]

        def calc_accuracy(group):
            if not group:
                return {"accuracy": 0, "correct": 0, "total": 0}
            correct = sum(1 for r in group if r['prediction_correct'])
            total = len(group)
            return {
                "accuracy": round((correct/total)*100, 1),
                "correct": correct,
                "total": total
            }

        return {
            "high_confidence_55plus": calc_accuracy(high_conf),
            "medium_confidence_45_55": calc_accuracy(medium_conf),
            "low_confidence_below_45": calc_accuracy(low_conf)
        }

    def get_team_predictions(self, team_name: str) -> Dict[str, Any]:
        """Get prediction accuracy for a specific team"""
        Pred = Query()
        team_preds = self.predictions.search(
            (Pred.team1 == team_name) | (Pred.team2 == team_name)
        )

        if not team_preds:
            return {"team": team_name, "predictions": 0}

        correct_when_predicted = 0
        total_predicted = 0

        for pred in team_preds:
            Res = Query()
            result = self.results.get(Res.prediction_id == pred['id'])
            if result:
                total_predicted += 1
                if result['prediction_correct'] and result['actual_winner'] == team_name:
                    correct_when_predicted += 1

        accuracy = (correct_when_predicted / total_predicted * 100) if total_predicted > 0 else 0

        return {
            "team": team_name,
            "predictions_made": len(team_preds),
            "correct_predictions": correct_when_predicted,
            "accuracy_when_predicted_to_win": round(accuracy, 1)
        }

    def generate_improvement_report(self) -> Dict[str, Any]:
        """Generate a report on what's working and what needs improvement"""
        overall = self.get_prediction_accuracy()
        by_confidence = self.get_prediction_by_confidence()
        all_results = self.results.all()

        if not all_results:
            return {"message": "No results yet to analyze"}

        # Find patterns in wrong predictions
        wrong_predictions = [r for r in all_results if not r['prediction_correct']]
        wrong_high_conf = [r for r in wrong_predictions if r['confidence_in_prediction'] >= 55]

        # Calculate average score differential in wrong predictions
        avg_wrong_diff = sum(abs(r.get('team1_score', 0) - r.get('team2_score', 0))
                            for r in wrong_predictions) / len(wrong_predictions) if wrong_predictions else 0

        report = {
            "overall_accuracy": overall,
            "accuracy_by_confidence": by_confidence,
            "areas_for_improvement": {
                "high_confidence_misses": len(wrong_high_conf),
                "message": "Focus on improving high-confidence predictions" if len(wrong_high_conf) > 2 else "High-confidence predictions are strong!"
            },
            "recommendations": []
        }

        # Add recommendations
        if by_confidence['high_confidence_55plus']['accuracy'] < 60:
            report['recommendations'].append("⚠️ High confidence predictions underperforming - may need weight adjustment")

        if by_confidence['low_confidence_below_45']['accuracy'] > 55:
            report['recommendations'].append("✅ Low confidence predictions doing well - current model is reliable")

        if len(all_results) < 10:
            report['recommendations'].append("📊 Need more data (10+ predictions) for meaningful analysis")

        return report

    def close(self):
        self.db.close()


if __name__ == "__main__":
    analysis = WatsonAnalysis()

    # Example usage:
    print("\n" + "="*80)
    print("WATSON ANALYSIS SYSTEM")
    print("="*80 + "\n")

    # Save a prediction (would happen in Discord bot)
    # analysis.save_prediction(
    #     "Team A vs Team B",
    #     "Team A", "Team B",
    #     "Team A",
    #     {"team1": {"probability": 65}, "team2": {"probability": 35}},
    #     {"team1": 120, "team2": 100}
    # )

    # Get accuracy
    accuracy = analysis.get_prediction_accuracy()
    print(f"📊 Prediction Accuracy: {accuracy['accuracy']}%")
    print(f"   Correct: {accuracy['correct']} / Total: {accuracy['total_predictions']}\n")

    # Get confidence analysis
    by_conf = analysis.get_prediction_by_confidence()
    print(f"🔍 Accuracy by Confidence Level:")
    print(f"   High (55%+): {by_conf['high_confidence_55plus']['accuracy']}%")
    print(f"   Medium (45-55%): {by_conf['medium_confidence_45_55']['accuracy']}%")
    print(f"   Low (<45%): {by_conf['low_confidence_below_45']['accuracy']}%\n")

    # Get improvement report
    report = analysis.generate_improvement_report()
    print(f"📈 Improvement Report:")
    if 'message' not in report:
        for rec in report.get('recommendations', []):
            print(f"   {rec}")

    analysis.close()
