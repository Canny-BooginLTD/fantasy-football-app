#!/usr/bin/env python3
"""Watson Fantasy Football Discord Bot"""

import discord
from discord.ext import commands
from watson_query import WatsonLeagueDB
from watson_predictor import WatsonPredictor
from watson_analysis import WatsonAnalysis
from team_abbrev import get_abbreviation, get_team_name, list_all_abbreviations, list_all_with_names
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Track recent command executions to prevent duplicates
_command_cache = {}

def _should_execute(cmd_name: str, user_id: int) -> bool:
    """Check if command should execute (prevent duplicates within 1 second)"""
    key = f"{cmd_name}_{user_id}"
    now = time.time()
    last_exec = _command_cache.get(key, 0)
    if now - last_exec < 1.0:
        return False
    _command_cache[key] = now
    return True

# Create bot with command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.members = False
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is now running!")
    print(f"Connected to Discord")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="fantasy football"))

# Track if bot is already connected to prevent double execution
_bot_ready = False

@bot.event
async def on_command_completion(ctx):
    """Runs after a command is executed"""
    pass

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    print(f"❌ Error: {error}")
    embed = discord.Embed(
        title="❌ Error",
        description=f"Something went wrong: {str(error)}",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command(name="all_odds", help="Show Vegas odds for all current week matchups")
async def all_odds(ctx):
    """Show Vegas moneyline odds for all current matchups"""
    # Prevent duplicate executions
    if not _should_execute("all_odds", ctx.author.id):
        return

    try:
        db = WatsonLeagueDB()
        current_season = max(db.get_seasons())
        matchups = db.get_matchups(current_season)
        db.close()

        predictor = WatsonPredictor()
        analysis = WatsonAnalysis()

        embed = discord.Embed(
            title=f"📊 Season {current_season} - All Matchup Odds",
            description="Vegas Moneyline Odds for Current Week",
            color=discord.Color.gold()
        )

        for i, matchup in enumerate(matchups, 1):
            home_team = matchup['home_team']
            away_team = matchup['away_team']

            prediction = predictor.predict_current(home_team, away_team)

            if "error" in prediction:
                embed.add_field(
                    name=f"Matchup {i}",
                    value=f"{home_team} vs {away_team}\n(Unable to calculate odds)",
                    inline=False
                )
                continue

            # AUTO-SAVE PREDICTION
            pred_id = analysis.save_prediction(
                f"{prediction['team1']['name']} vs {prediction['team2']['name']}",
                prediction['team1']['name'],
                prediction['team2']['name'],
                prediction['predicted_winner'],
                prediction['moneyline_odds'],
                {
                    "team1": prediction['team1']['weighted_score'],
                    "team2": prediction['team2']['weighted_score']
                }
            )

            ml = prediction['moneyline_odds']
            t1 = ml['team1']
            t2 = ml['team2']

            odds1_str = f"{t1['odds']:+d}" if t1['odds'] < 0 else f"+{t1['odds']}"
            odds2_str = f"{t2['odds']:+d}" if t2['odds'] < 0 else f"+{t2['odds']}"

            matchup_text = (
                f"**{t1['name']}** ({odds1_str}) {t1['probability']}%\n"
                f"vs\n"
                f"**{t2['name']}** ({odds2_str}) {t2['probability']}%\n"
                f"`ID: {pred_id}`"
            )

            embed.add_field(
                name=f"Matchup {i}: {prediction['predicted_winner']} 🏆",
                value=matchup_text,
                inline=False
            )

        predictor.close()
        analysis.close()
        embed.set_footer(text="80% current projections + 20% historical | Vegas moneyline odds | ✅ All saved automatically")
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="ping", help="Test if bot is alive")
async def ping(ctx):
    """Simple ping command to test bot"""
    await ctx.send(f"🏈 Pong! Bot is alive!")

@bot.command(name="seasons", help="List all available seasons")
async def seasons(ctx):
    """List all available seasons"""
    try:
        db = WatsonLeagueDB()
        available_seasons = db.get_seasons()
        db.close()

        embed = discord.Embed(
            title="🏈 Available Seasons",
            description=f"**Seasons:** {', '.join(map(str, available_seasons))}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="standings", help="!standings <year> - Show standings for a season")
async def standings(ctx, year: int):
    """Show standings for a season"""
    try:
        db = WatsonLeagueDB()
        teams = db.get_standings(year, limit=10)
        db.close()

        if not teams:
            embed = discord.Embed(title="❌ No Data", description=f"No data found for {year}", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        standings_text = ""
        for i, team in enumerate(teams, 1):
            record = f"{team['wins']}-{team['losses']}"
            standings_text += f"`{i}. {team['team_name']:<25} {record:<8} {team['points_for']:>8.1f} pts`\n"

        embed = discord.Embed(
            title=f"📊 Season {year} Standings",
            description=standings_text,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="matchups", help="!matchups <year> - Show matchups for a season")
async def matchups(ctx, year: int):
    """Show matchups for a season"""
    try:
        db = WatsonLeagueDB()
        matches = db.get_matchups(year)
        db.close()

        if not matches:
            embed = discord.Embed(title="❌ No Data", description=f"No matchups found for {year}", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        for i, match in enumerate(matches, 1):
            home = match['home_team']
            home_score = match['home_score']
            away = match['away_team']
            away_score = match['away_score']

            winner = "🏆 " + (home if home_score > away_score else away)

            matchup_text = f"**{home}** {home_score:.2f}\nvs\n**{away}** {away_score:.2f}"

            embed = discord.Embed(
                title=f"Matchup {i} - Season {year}",
                description=matchup_text,
                color=discord.Color.gold()
            )
            embed.add_field(name="Winner", value=winner, inline=False)
            await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="matchup_details", help="!matchup_details <year> <matchup_number> - Show player details for a matchup")
async def matchup_details(ctx, year: int, matchup_num: int):
    """Show detailed player stats for a specific matchup"""
    try:
        db = WatsonLeagueDB()
        matches = db.get_matchups(year)
        db.close()

        if matchup_num < 1 or matchup_num > len(matches):
            embed = discord.Embed(title="❌ Error", description=f"Matchup {matchup_num} not found", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        match = matches[matchup_num - 1]
        home_team = match['home_team']
        home_score = match['home_score']
        away_team = match['away_team']
        away_score = match['away_score']
        home_players = match.get('home_players', [])
        away_players = match.get('away_players', [])

        winner = home_team if home_score > away_score else away_team

        # Home team embed - show all players
        home_text = ""
        for player in home_players:  # Show ALL players
            name = player.get('name', 'N/A')
            pts = player.get('points', 0)
            home_text += f"`{name:<25} {pts:>6.1f} pts`\n"

        embed1 = discord.Embed(
            title=f"Matchup {matchup_num} - Season {year}: {home_team} ({home_score:.2f})",
            description=home_text or "(No player data)",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed1)

        # Away team embed - show all players
        away_text = ""
        for player in away_players:  # Show ALL players
            name = player.get('name', 'N/A')
            pts = player.get('points', 0)
            away_text += f"`{name:<25} {pts:>6.1f} pts`\n"

        embed2 = discord.Embed(
            title=f"{away_team} ({away_score:.2f})",
            description=away_text or "(No player data)",
            color=discord.Color.gold()
        )
        embed2.add_field(name="Winner", value=f"🏆 {winner}", inline=False)
        await ctx.send(embed=embed2)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="predict_current", help="!predict_current <team1> vs <team2> [, <team3> vs <team4>] - Predict one or multiple matchups")
async def predict_current(ctx, *, teams: str):
    """Predict CURRENT matchup(s) using player projections with Vegas moneyline odds.
    Supports multiple matchups separated by comma, semicolon, or newline."""
    try:
        raw = (teams or "").strip()
        if not raw:
            embed = discord.Embed(title="❌ Error", description="Format: !predict_current <team1> vs <team2>\nOr multiple: !predict_current VG vs SF, MVDT vs TCR", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        # Normalize separators into comma
        normalized = raw.replace("\n", ",").replace(";", ",")
        segments = [s.strip() for s in normalized.split(",") if s.strip()]

        predictor = WatsonPredictor()
        analysis = WatsonAnalysis()
        embeds = []

        for segment in segments:
            # Find first " vs " (case-insensitive)
            low = segment.lower()
            idx = low.find(" vs ")

            if idx == -1:
                embeds.append(discord.Embed(title="❌ Invalid Matchup", description=f"Could not parse: `{segment}`\nUse `team1 vs team2`", color=discord.Color.red()))
                continue

            team1_input = segment[:idx].strip()
            team2_input = segment[idx + 4:].strip()

            if not team1_input or not team2_input:
                embeds.append(discord.Embed(title="❌ Invalid Matchup", description=f"Could not parse: `{segment}`", color=discord.Color.red()))
                continue

            # Resolve aliases/abbreviations
            team1 = get_team_name(team1_input) or team1_input
            team2 = get_team_name(team2_input) or team2_input

            prediction = predictor.predict_current(team1, team2)

            if "error" in prediction:
                embeds.append(discord.Embed(title="❌ Error", description=f"{team1_input} vs {team2_input}: {prediction['error']}", color=discord.Color.red()))
                continue

            # AUTO-SAVE PREDICTION
            pred_id = analysis.save_prediction(
                f"{prediction['team1']['name']} vs {prediction['team2']['name']}",
                prediction['team1']['name'],
                prediction['team2']['name'],
                prediction['predicted_winner'],
                prediction['moneyline_odds'],
                {"team1": prediction['team1']['weighted_score'], "team2": prediction['team2']['weighted_score']}
            )

            ml = prediction['moneyline_odds']
            t1 = ml['team1']
            t2 = ml['team2']
            odds1_str = f"{t1['odds']:+d}" if t1['odds'] < 0 else f"+{t1['odds']}"
            odds2_str = f"{t2['odds']:+d}" if t2['odds'] < 0 else f"+{t2['odds']}"

            t1_data = prediction['team1']
            t2_data = prediction['team2']

            embed = discord.Embed(title="🔮 Current Matchup Prediction (Vegas Odds)", description=f"**{prediction['matchup']}**", color=discord.Color.purple())
            embed.add_field(name="Predicted Winner", value=f"🏆 {prediction['predicted_winner']}", inline=False)
            embed.add_field(
                name=f"{t1['name']} ({get_abbreviation(t1['name'])}) {'(Favorite)' if t1['odds'] < 0 else '(Underdog)'}",
                value=f"**Odds:** {odds1_str}\n**Probability:** {t1['probability']}%", inline=True
            )
            embed.add_field(
                name=f"{t2['name']} ({get_abbreviation(t2['name'])}) {'(Favorite)' if t2['odds'] < 0 else '(Underdog)'}",
                value=f"**Odds:** {odds2_str}\n**Probability:** {t2['probability']}%", inline=True
            )
            embed.add_field(name=f"{t1_data['name']} Breakdown", value=f"Projection: {t1_data['projection']}\nHistorical: {t1_data['historical_avg']}\n**Weighted: {t1_data['weighted_score']}**", inline=True)
            embed.add_field(name=f"{t2_data['name']} Breakdown", value=f"Projection: {t2_data['projection']}\nHistorical: {t2_data['historical_avg']}\n**Weighted: {t2_data['weighted_score']}**", inline=True)
            embed.add_field(name="Prediction ID", value=f"`{pred_id}`", inline=False)
            pred_type = prediction.get('prediction_type', '✅ Current week with player projections')
            embed.add_field(name="💾 Status", value=f"{pred_type}\n✅ Automatically saved for tracking", inline=False)
            embed.set_footer(text="80% current projections + 20% historical | Vegas moneyline implied odds")
            embeds.append(embed)

        predictor.close()
        analysis.close()

        if embeds:
            for embed in embeds:
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="❌ Error", description="No valid matchups found", color=discord.Color.red())
            await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="predict_matchup", help="!predict_matchup <team1> vs <team2> - Predict using historical data")
async def predict_matchup(ctx, *, teams: str):
    """Predict outcome of a matchup"""
    try:
        # Parse team names from input (format: "Team1 vs Team2")
        if " vs " in teams:
            team1, team2 = teams.split(" vs ")
            team1 = team1.strip()
            team2 = team2.strip()
        else:
            embed = discord.Embed(title="❌ Error", description="Format: !predict_matchup <team1> vs <team2>", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        predictor = WatsonPredictor()
        prediction = predictor.predict_matchup(team1, team2)
        predictor.close()

        embed = discord.Embed(
            title="🔮 Matchup Prediction",
            description=f"**{prediction['matchup']}**",
            color=discord.Color.purple()
        )
        embed.add_field(name="Predicted Winner", value=f"🏆 {prediction['predicted_winner']}", inline=False)
        embed.add_field(name="Confidence", value=f"{prediction['confidence']}%", inline=False)
        embed.add_field(name=f"{team1} Avg Points", value=f"{prediction['team1_avg_points']}", inline=True)
        embed.add_field(name=f"{team2} Avg Points", value=f"{prediction['team2_avg_points']}", inline=True)
        embed.add_field(name=f"{team1} Win Rate", value=f"{prediction['team1_win_rate']}%", inline=True)
        embed.add_field(name=f"{team2} Win Rate", value=f"{prediction['team2_win_rate']}%", inline=True)
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="predict_season", help="!predict_season <year> - Predict season winner")
async def predict_season(ctx, year: int):
    """Predict season winner based on historical performance"""
    try:
        predictor = WatsonPredictor()
        season_pred = predictor.predict_season_winner(year)
        predictor.close()

        predictions_text = ""
        for i, team in enumerate(season_pred['top_contenders'], 1):
            predictions_text += f"{i}. **{team['team']}** - {team['win_probability']}% chance\n"
            predictions_text += f"   ↳ Avg Points: {team['avg_points']}\n"

        embed = discord.Embed(
            title=f"🏆 Season {year} Predictions",
            description="Top Contenders Based on Historical Performance:",
            color=discord.Color.gold()
        )
        embed.add_field(name="Top 3 Teams", value=predictions_text, inline=False)
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="head_to_head", help="!head_to_head <team1> vs <team2> - Show head-to-head history")
async def head_to_head(ctx, *, teams: str):
    """Show head-to-head matchup history"""
    try:
        if " vs " in teams:
            team1, team2 = teams.split(" vs ")
            team1 = team1.strip()
            team2 = team2.strip()
        else:
            embed = discord.Embed(title="❌ Error", description="Format: !head_to_head <team1> vs <team2>", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        predictor = WatsonPredictor()
        h2h = predictor.head_to_head(team1, team2)
        predictor.close()

        history_text = ""
        for match in h2h['matchup_history']:
            winner = match['home_team'] if match['home_score'] > match['away_score'] else match['away_team']
            history_text += f"**{match['season']}**: {match['home_team']} ({match['home_score']:.1f}) vs {match['away_team']} ({match['away_score']:.1f})\n"

        embed = discord.Embed(
            title="⚔️ Head-to-Head History",
            description=f"**{team1}** vs **{team2}**",
            color=discord.Color.red()
        )
        embed.add_field(name="Record", value=h2h['h2h_record'], inline=True)
        embed.add_field(name="Total Matchups", value=h2h['total_matchups'], inline=True)
        embed.add_field(name="Matchup History", value=history_text or "No matchups found", inline=False)
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="teams", help="List all league teams")
async def teams(ctx):
    """List all teams in the league"""
    try:
        db = WatsonLeagueDB()
        latest_season = max(db.get_seasons())
        teams_list = db.get_standings(latest_season, limit=100)
        db.close()

        teams_text = ""
        for i, team in enumerate(teams_list, 1):
            teams_text += f"{i}. {team['team_name']}\n"

        embed = discord.Embed(
            title=f"🏈 League Teams (Season {latest_season})",
            description=teams_text,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="team_stats", help="!team_stats <team_name> - Show all-time team stats")
async def team_stats(ctx, *, team_name: str):
    """Show all-time stats for a team"""
    try:
        predictor = WatsonPredictor()
        stats = predictor.get_team_stats(team_name)
        predictor.close()

        if stats['seasons_played'] == 0:
            # Get list of available teams
            db = WatsonLeagueDB()
            latest_season = max(db.get_seasons())
            teams_list = db.get_standings(latest_season, limit=100)
            db.close()

            teams_text = "Available teams:\n"
            for team in teams_list:
                teams_text += f"• {team['team_name']}\n"

            embed = discord.Embed(
                title=f"❌ Team '{team_name}' not found",
                description=teams_text,
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"📊 {stats['team_name']} All-Time Stats",
            color=discord.Color.blue()
        )
        embed.add_field(name="Record", value=f"{stats['total_wins']}-{stats['total_losses']}", inline=True)
        embed.add_field(name="Win Rate", value=f"{stats['win_rate']*100:.1f}%", inline=True)
        embed.add_field(name="Total Points", value=f"{stats['total_points']:.1f}", inline=True)
        embed.add_field(name="Avg Points/Season", value=f"{stats['avg_points_per_season']:.1f}", inline=True)
        embed.add_field(name="Seasons Played", value=stats['seasons_played'], inline=True)
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="save_prediction", help="!save_prediction <team1> vs <team2> - Save a prediction for later analysis")
async def save_prediction(ctx, *, teams: str):
    """Save current prediction for accuracy tracking"""
    try:
        if " vs " not in teams:
            embed = discord.Embed(title="❌ Error", description="Format: !save_prediction <team1> vs <team2>", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        team1, team2 = teams.split(" vs ")
        team1 = team1.strip()
        team2 = team2.strip()

        predictor = WatsonPredictor()
        prediction = predictor.predict_current(team1, team2)
        predictor.close()

        if "error" in prediction:
            embed = discord.Embed(title="❌ Error", description=prediction['error'], color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        analysis = WatsonAnalysis()
        pred_id = analysis.save_prediction(
            f"{team1} vs {team2}",
            prediction['team1']['name'],
            prediction['team2']['name'],
            prediction['predicted_winner'],
            prediction['moneyline_odds'],
            {
                "team1": prediction['team1']['weighted_score'],
                "team2": prediction['team2']['weighted_score']
            }
        )
        analysis.close()

        embed = discord.Embed(
            title="✅ Prediction Saved",
            description=f"**{prediction['matchup']}**\n**Prediction ID:** `{pred_id}`",
            color=discord.Color.green()
        )
        embed.add_field(name="Predicted Winner", value=f"🏆 {prediction['predicted_winner']}", inline=False)

        ml = prediction['moneyline_odds']
        embed.add_field(
            name="Vegas Odds",
            value=f"{ml['team1']['name']}: {ml['team1']['odds']:+d} ({ml['team1']['probability']}%)\nvs\n{ml['team2']['name']}: {ml['team2']['odds']:+d} ({ml['team2']['probability']}%)",
            inline=False
        )
        embed.set_footer(text="Use !record_result to log the actual outcome")
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="record_result", help="!record_result <prediction_id> <winner> <team1_score> <team2_score>")
async def record_result(ctx, pred_id: str, winner: str, team1_score: float, team2_score: float):
    """Record the actual result of a matchup"""
    try:
        analysis = WatsonAnalysis()
        analysis.record_result(pred_id, winner, team1_score, team2_score)
        analysis.close()

        embed = discord.Embed(
            title="✅ Result Recorded",
            description=f"Prediction ID: `{pred_id}`\nActual Winner: **{winner}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Final Score", value=f"Team 1: {team1_score}\nTeam 2: {team2_score}", inline=False)
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="prediction_accuracy", help="Show overall prediction accuracy")
async def prediction_accuracy(ctx):
    """Show prediction accuracy and analysis"""
    try:
        analysis = WatsonAnalysis()
        accuracy = analysis.get_prediction_accuracy()
        by_conf = analysis.get_prediction_by_confidence()
        report = analysis.generate_improvement_report()
        analysis.close()

        embed = discord.Embed(
            title="📊 Prediction Analysis",
            color=discord.Color.blue()
        )

        if accuracy['total_predictions'] == 0:
            embed.add_field(name="No Data", value="No predictions recorded yet. Use !save_prediction to start tracking.", inline=False)
            await ctx.send(embed=embed)
            return

        embed.add_field(
            name="Overall Accuracy",
            value=f"**{accuracy['accuracy']}%** ({accuracy['correct']}/{accuracy['total_predictions']})",
            inline=False
        )

        embed.add_field(
            name="High Confidence (55%+)",
            value=f"{by_conf['high_confidence_55plus']['accuracy']}% ({by_conf['high_confidence_55plus']['correct']}/{by_conf['high_confidence_55plus']['total']})",
            inline=True
        )

        embed.add_field(
            name="Medium Confidence (45-55%)",
            value=f"{by_conf['medium_confidence_45_55']['accuracy']}% ({by_conf['medium_confidence_45_55']['correct']}/{by_conf['medium_confidence_45_55']['total']})",
            inline=True
        )

        embed.add_field(
            name="Low Confidence (<45%)",
            value=f"{by_conf['low_confidence_below_45']['accuracy']}% ({by_conf['low_confidence_below_45']['correct']}/{by_conf['low_confidence_below_45']['total']})",
            inline=True
        )

        if report.get('recommendations'):
            rec_text = "\n".join(report['recommendations'])
            embed.add_field(name="Recommendations", value=rec_text, inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="team_abbrev", help="Show all team abbreviations and player names")
async def team_abbrev(ctx):
    """Show all team abbreviations and player names for quick reference"""
    try:
        abbrev_list = list_all_with_names()
        embed = discord.Embed(
            title="🏈 Team Abbreviations & Player Names",
            description=f"```\n{abbrev_list}\n```",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use abbreviations, team names, or first names! E.g.: !predict_current VG vs SF or !predict_current Rahul vs Lil")
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="help_watson", help="Show Watson commands")
async def help_watson(ctx):
    """Show all Watson commands"""
    embed = discord.Embed(
        title="🏈 Watson Fantasy Football Bot Commands",
        description="Use these commands to query your league data and predictions:",
        color=discord.Color.green()
    )

    # General commands
    embed.add_field(name="📋 General Commands", value="", inline=False)
    embed.add_field(name="!team_abbrev", value="Show all team abbreviations", inline=False)
    embed.add_field(name="!teams", value="List all league teams", inline=False)
    embed.add_field(name="!seasons", value="List all available seasons", inline=False)
    embed.add_field(name="!standings <year>", value="Show standings for a season (e.g., !standings 2024)", inline=False)
    embed.add_field(name="!matchups <year>", value="Show all matchups for a season (e.g., !matchups 2024)", inline=False)
    embed.add_field(name="!matchup_details <year> <num>", value="Show player stats for a matchup (e.g., !matchup_details 2024 1)", inline=False)

    # Prediction commands
    embed.add_field(name="🔮 Prediction Commands", value="", inline=False)
    embed.add_field(name="!all_odds", value="Show Vegas odds for all current matchups", inline=False)
    embed.add_field(name="!team_stats <team_name>", value="Show all-time stats for a team", inline=False)
    embed.add_field(name="!predict_current <team1> vs <team2>", value="Predict matchup with Vegas odds", inline=False)
    embed.add_field(name="!predict_season <year>", value="Predict season winner (e.g., !predict_season 2024)", inline=False)
    embed.add_field(name="!head_to_head <team1> vs <team2>", value="Show head-to-head history", inline=False)

    # Analysis commands
    embed.add_field(name="📈 Analysis & Learning Commands", value="", inline=False)
    embed.add_field(name="!save_prediction <team1> vs <team2>", value="Save a prediction for accuracy tracking", inline=False)
    embed.add_field(name="!record_result <pred_id> <winner> <score1> <score2>", value="Log actual matchup result", inline=False)
    embed.add_field(name="!prediction_accuracy", value="Show prediction accuracy and improvement recommendations", inline=False)

    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in .env file")
        print("Please add your Discord bot token to watson-fantasy-ai/.env")
        exit(1)

    print("🏈 Starting Watson Fantasy Football Discord Bot...")
    bot.run(DISCORD_TOKEN)

