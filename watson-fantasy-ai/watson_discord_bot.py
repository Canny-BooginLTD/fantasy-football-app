#!/usr/bin/env python3
"""Watson Fantasy Football Discord Bot"""

import discord
from discord.ext import commands
from watson_query import WatsonLeagueDB
from watson_predictor import WatsonPredictor
from watson_analysis import WatsonAnalysis
from watson_result_scraper import WatsonResultScraper
from sleeper_scraper import SleeperScraper
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
        # Case-insensitive split
        teams_lower = teams.lower()
        if " vs " not in teams_lower:
            embed = discord.Embed(title="❌ Error", description="Format: !predict_matchup <team1> vs <team2>", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        idx = teams_lower.find(" vs ")
        team1_input = teams[:idx].strip()
        team2_input = teams[idx + 4:].strip()

        # Resolve abbreviations/aliases
        team1 = get_team_name(team1_input) or team1_input
        team2 = get_team_name(team2_input) or team2_input

        predictor = WatsonPredictor()
        prediction = predictor.predict_matchup(team1, team2)
        predictor.close()

        if "error" in prediction:
            embed = discord.Embed(title="❌ Error", description=prediction['error'], color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🔮 Matchup Prediction (Historical)",
            description=f"**{prediction['matchup']}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Predicted Winner", value=f"🏆 {prediction['predicted_winner']}", inline=False)
        embed.add_field(name="Confidence", value=f"{prediction.get('confidence', 'N/A')}%", inline=False)
        embed.add_field(name="Team 1 Avg Points", value=f"{prediction.get('team1_avg', 'N/A')}", inline=True)
        embed.add_field(name="Team 2 Avg Points", value=f"{prediction.get('team2_avg', 'N/A')}", inline=True)
        embed.add_field(name="Team 1 Win Rate", value=f"{prediction.get('team1_winrate', 'N/A')}%", inline=True)
        embed.add_field(name="Team 2 Win Rate", value=f"{prediction.get('team2_winrate', 'N/A')}%", inline=True)
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="predict_season", help="!predict_season [year] - Predict season winner")
async def predict_season(ctx, year: int = None):
    """Predict season winner based on historical performance"""
    try:
        predictor = WatsonPredictor()
        prediction = predictor.predict_season_winner(year)
        predictor.close()

        embed = discord.Embed(
            title=f"🏆 Season {prediction['year']} Winner Prediction",
            description="Based on historical win rates and current performance",
            color=discord.Color.gold()
        )

        top_3 = prediction['top_3']
        for i, team in enumerate(top_3, 1):
            medal = ["🥇", "🥈", "🥉"][i-1]
            embed.add_field(
                name=f"{medal} #{i} - {team['team']}",
                value=f"Win Probability: **{team['win_probability']}%**\nCurrent: {team['current_record']}\nPoints: {team['current_points']}\nHistorical Avg: {team['historical_avg']}",
                inline=False
            )

        embed.set_footer(text="Prediction based on historical win rates and current season performance")
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="head_to_head", help="!head_to_head <team1> vs <team2> - Show head-to-head history")
async def head_to_head(ctx, *, teams: str):
    """Show head-to-head matchup history"""
    try:
        # Case-insensitive split
        teams_lower = teams.lower()
        if " vs " not in teams_lower:
            embed = discord.Embed(title="❌ Error", description="Format: !head_to_head <team1> vs <team2>", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        idx = teams_lower.find(" vs ")
        team1_input = teams[:idx].strip()
        team2_input = teams[idx + 4:].strip()

        # Resolve abbreviations/aliases
        team1 = get_team_name(team1_input) or team1_input
        team2 = get_team_name(team2_input) or team2_input

        predictor = WatsonPredictor()
        h2h = predictor.head_to_head(team1, team2)
        predictor.close()

        if "error" in h2h:
            embed = discord.Embed(title="❌ Error", description=h2h['error'], color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="⚔️ Head-to-Head History",
            description=f"**{h2h['team1']}** vs **{h2h['team2']}**",
            color=discord.Color.red()
        )
        embed.add_field(name="Record", value=h2h['record'], inline=True)
        embed.add_field(name="Total Matchups", value=h2h['matchups'], inline=True)
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
async def save_prediction(ctx, *, teams: str = None):
    """Save current prediction for accuracy tracking"""
    try:
        if not teams or " vs " not in teams:
            embed = discord.Embed(
                title="ℹ️ Note",
                description="Predictions are **automatically saved** when you use `!predict_current`!\n\nBut you can manually save with:\n`!save_prediction <team1> vs <team2>`",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        idx = teams.lower().find(" vs ")
        team1_input = teams[:idx].strip()
        team2_input = teams[idx + 4:].strip()

        # Resolve aliases
        team1 = get_team_name(team1_input) or team1_input
        team2 = get_team_name(team2_input) or team2_input

        predictor = WatsonPredictor()
        prediction = predictor.predict_current(team1, team2)
        predictor.close()

        if "error" in prediction:
            embed = discord.Embed(title="❌ Error", description=prediction['error'], color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        analysis = WatsonAnalysis()
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

@bot.command(name="refresh_projections", help="Sync Sleeper player projections for ESPN rosters")
async def refresh_projections(ctx, week: str = None):
    """Sync Sleeper player projections and map to ESPN rosters"""
    try:
        # Convert week to int, default to 1
        if week is None:
            week_num = 1
        else:
            try:
                week_num = int(week)
            except ValueError:
                week_num = 1

        scraper = SleeperScraper()
        result = scraper.sync_espn_rosters_with_sleeper(week_num)

        if result:
            matchups = result.get('matchups', [])
            embed = discord.Embed(
                title="✅ Projections Synced",
                description=f"Week {week_num} - Mapped Sleeper player stats to ESPN rosters",
                color=discord.Color.green()
            )
            embed.add_field(name="Matchups", value=f"{len(matchups)} matchups updated", inline=True)

            # Show sample
            if matchups:
                m = matchups[0]
                embed.add_field(
                    name="Sample",
                    value=f"{m['home_team']}: {m['home_projection']} pts\nvs\n{m['away_team']}: {m['away_projection']} pts",
                    inline=False
                )

            embed.set_footer(text="✅ Ready for predictions! Sleeper player stats now loaded.")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Sync Failed",
                description="Could not fetch Sleeper player projections",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="sync_results", help="Auto-sync completed matchup results (Mondays only)")
async def sync_results(ctx):
    """Automatically scan for completed matchups and record results.
    Only runs on Mondays after league week completes (Thu-Mon schedule)."""
    try:
        from datetime import datetime

        # Check if today is Monday (weekday() returns 0 for Monday)
        today = datetime.now()
        if today.weekday() != 0:  # 0 = Monday
            day_name = today.strftime("%A")
            embed = discord.Embed(
                title="⏰ Not Yet",
                description=f"Today is {day_name}. Results can only be synced on **Monday** after the league week ends.\n\nCome back Monday night!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        scraper = WatsonResultScraper()
        summary = scraper.sync_results(2026)
        scraper.close()

        embed = discord.Embed(
            title="📊 Weekly Results Sync",
            description=f"Season {summary['season']} - Monday Night Results",
            color=discord.Color.green()
        )

        embed.add_field(name="Processed", value=f"{summary['processed']} matchups", inline=True)
        embed.add_field(name="Newly Recorded", value=f"{summary['newly_recorded']} results", inline=True)
        embed.add_field(name="Already Graded", value=f"{summary['already_graded']}", inline=True)
        embed.add_field(name="No Prediction Found", value=f"{summary['no_prediction_found']}", inline=True)

        if summary['results']:
            results_text = ""
            for result in summary['results']:
                status = "✅" if result['correct'] else "❌"
                results_text += f"{status} {result['matchup']}\n"
                results_text += f"   Pred: {result['predicted_winner']} | Actual: {result['actual_winner']} ({result['scores']})\n"
            embed.add_field(name="Newly Recorded", value=results_text, inline=False)
        else:
            embed.add_field(name="Status", value="No new results to record", inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="sync", help="!sync [year] - Pull live ESPN scores/standings (official source) into the DB")
async def sync_espn(ctx, year: int = 2026):
    """Refresh actual scores, player points, and standings from ESPN"""
    try:
        import asyncio
        from espn_update import update_season

        msg = await ctx.send(f"📡 Pulling live ESPN data for season {year}...")
        result = await asyncio.to_thread(update_season, year)

        embed = discord.Embed(
            title="✅ ESPN Sync Complete",
            description=f"Season {result['season']} updated from ESPN (official league source)",
            color=discord.Color.green()
        )
        embed.add_field(name="Matchups", value=f"{result['matchups']} through week {result['week']}", inline=True)
        await msg.edit(content=None, embed=embed)

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

@bot.command(name="player", help="!player <player_name> - Show player stats and projections")
async def player(ctx, *, player_name: str):
    """Look up individual player stats and projections"""
    try:
        db = WatsonLeagueDB()
        current_season = max(db.get_seasons())
        matchups = db.get_matchups(current_season)
        db.close()

        # Search for player across all matchups
        found_players = []
        player_lower = player_name.lower()

        for matchup in matchups:
            for player in matchup.get('home_players', []):
                if player_lower in player.get('name', '').lower():
                    found_players.append({
                        "name": player.get('name'),
                        "position": player.get('position'),
                        "points": player.get('points', 0),
                        "projected_points": player.get('projected_points', 0),
                        "slot": player.get('slot'),
                        "team": matchup['home_team']
                    })

            for player in matchup.get('away_players', []):
                if player_lower in player.get('name', '').lower():
                    found_players.append({
                        "name": player.get('name'),
                        "position": player.get('position'),
                        "points": player.get('points', 0),
                        "projected_points": player.get('projected_points', 0),
                        "slot": player.get('slot'),
                        "team": matchup['away_team']
                    })

        if not found_players:
            embed = discord.Embed(
                title="❌ Player Not Found",
                description=f"No player found matching '{player_name}'\n\nTry searching by first name, last name, or partial name.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Show all matching players
        for player in found_players:
            embed = discord.Embed(
                title=f"🏈 {player['name']}",
                description=f"**{player['position']}** | {player['team']}",
                color=discord.Color.green()
            )
            embed.add_field(name="Actual Points", value=f"{player['points']:.1f}", inline=True)
            embed.add_field(name="Projected Points", value=f"{player['projected_points']:.1f}", inline=True)
            if player['slot']:
                embed.add_field(name="Slot", value=player['slot'], inline=True)
            await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="project", help="!project <player1> vs <player2> - Compare projections with boom/bust calls")
async def project(ctx, *, text: str):
    """Compare player projections head-to-head with a boom or bust call for each"""
    try:
        # Strip filler words so "!project these players josh allen vs joe burrow" works
        cleaned = text.lower()
        for filler in ["these players", "the players", "players", "please", "project"]:
            cleaned = cleaned.replace(filler, "")
        names = [n.strip() for n in cleaned.split(" vs ") if n.strip()]

        if len(names) < 2:
            await ctx.send("Usage: `!project <player1> vs <player2>` (e.g., `!project josh allen vs joe burrow`)")
            return

        db = WatsonLeagueDB()
        current_season = max(db.get_seasons())
        matchups = db.get_matchups(current_season)
        db.close()

        def collect(name_lower):
            """Gather all weekly entries for a player this season"""
            entries = []
            for m in matchups:
                for p in m.get('home_players', []) + m.get('away_players', []):
                    if name_lower in p.get('name', '').lower():
                        entries.append(p)
            return entries

        results = []
        for name in names:
            entries = collect(name)
            if not entries:
                results.append({"name": name, "found": False})
                continue
            latest = entries[-1]
            scored = [e.get('points', 0) or 0 for e in entries[:-1]]
            avg = sum(scored) / len(scored) if scored else 0
            proj = latest.get('projected_points', 0) or 0
            if avg and proj >= avg * 1.1:
                call = "💥 BOOM"
            elif avg and proj <= avg * 0.9:
                call = "🧨 BUST"
            else:
                call = "😐 PUSH"
            results.append({
                "name": latest.get('name'), "found": True, "position": latest.get('position'),
                "proj": proj, "avg": avg, "call": call
            })

        embed = discord.Embed(title="🔮 Player Projection Battle", color=discord.Color.purple())
        found = [r for r in results if r["found"]]
        for r in results:
            if not r["found"]:
                embed.add_field(name=f"❓ {r['name'].title()}", value="Not found on any roster", inline=False)
            else:
                embed.add_field(
                    name=f"{r['call']} — {r['name']} ({r['position']})",
                    value=f"Projected: **{r['proj']:.1f}** | Season avg: {r['avg']:.1f}",
                    inline=False
                )
        if len(found) >= 2:
            winner = max(found, key=lambda r: r['proj'])
            embed.add_field(name="🏆 Edge", value=f"**{winner['name']}** by projection", inline=False)

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
    embed.add_field(name="!sync [year]", value="Pull live ESPN scores/standings (official source)", inline=False)
    embed.add_field(name="!team_abbrev", value="Show all team abbreviations", inline=False)
    embed.add_field(name="!teams", value="List all league teams", inline=False)
    embed.add_field(name="!player <name>", value="Look up player stats (e.g., !player josh allen)", inline=False)
    embed.add_field(name="!project <p1> vs <p2>", value="Boom/bust projection battle (e.g., !project josh allen vs joe burrow)", inline=False)
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

