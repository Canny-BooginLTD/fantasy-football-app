# Watson Fantasy Football Discord Bot Setup

## Quick Start

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and name it "Watson"
3. Go to "Bot" section and click "Add Bot"
4. Under TOKEN, click "Copy" - **this is your DISCORD_TOKEN**
5. Under "OAuth2" → "URL Generator":
   - Select scopes: `bot`
   - Select permissions: `Send Messages`, `Embed Links`, `Read Messages`
   - Copy the generated URL and open it to invite the bot to your server

### 2. Add Your Discord Token

Edit `watson-fantasy-ai/.env`:
```
DISCORD_TOKEN=your_copied_token_here
```

### 3. Run the Bot

```bash
cd /Users/rahulsaikilambi/PycharmProjects/fantasy-football-app/watson-fantasy-ai && \
source ../venv/bin/activate && \
python watson_discord_bot.py
```

Keep this running in a terminal window!

## Bot Commands

### View Available Seasons
```
!seasons
```

### Show Standings for a Season
```
!standings 2024
!standings 2021
```

### Show All Matchups for a Season
```
!matchups 2024
```

### Show Player Details for a Specific Matchup
```
!matchup_details 2024 1
!matchup_details 2022 3
```

### Show Help
```
!help_watson
```

## Example Usage

```
User: !seasons
Bot: 🏈 Available Seasons: 2021, 2022, 2023, 2024, 2025, 2026

User: !standings 2024
Bot: (Shows all 10 teams with records and points)

User: !matchups 2024
Bot: (Shows each matchup with scores)

User: !matchup_details 2024 1
Bot: (Shows all players and their points for matchup 1)
```

## Keep Bot Running (Optional - macOS)

To run the bot in the background permanently, create a LaunchAgent:

```bash
cat > ~/Library/LaunchAgents/com.watson.discord.bot.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.watson.discord.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/rahulsaikilambi/PycharmProjects/fantasy-football-app/venv/bin/python</string>
        <string>/Users/rahulsaikilambi/PycharmProjects/fantasy-football-app/watson-fantasy-ai/watson_discord_bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/rahulsaikilambi/PycharmProjects/fantasy-football-app/watson-fantasy-ai</string>
    <key>StandardOutPath</key>
    <string>/tmp/watson_bot.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/watson_bot_error.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.watson.discord.bot.plist
```

Done! 🎉

