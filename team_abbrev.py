#!/usr/bin/env python3
"""Watson Team Abbreviations & Aliases"""

# Current season (2026) teams - PRIMARY
CURRENT_SEASON_TEAMS = {
    "Vancouver Gingerboogmen": "VG",
    "TOP 5 TLAW": "T5",
    "Sheen's Fastballs": "SF",
    "LuLu Feet Pix II": "LFP",
    "Michael Vick Did His Time": "MVDT",
    "Chinese Kicker": "CK",
    "Lauderdale Muneymen 💵": "LM",
    "The ChiRahuls": "TCR",
    "Duval Sixers": "DS",
    "Free R. Kelly": "FRK",
}

# Historical teams (2021-2025)
HISTORICAL_TEAMS = {
    # 2025 Teams
    "Sheen's Fastballs (2025)": "SF",
    "Chinese Kicker (2025)": "CK",
    "Etienne Butt": "EB",
    "LuLu Feet Pix": "LFP",
    "Free R. Kelly (2025)": "FRK",
    "TOP 5 TLAW (2025)": "T5",
    "No Russell Wilson?": "NRW",
    "Vancouver Gingerboogmen (2025)": "VG",
    "Lauderdale Muneymen 💵 (2025)": "LM",
    "Michael Vick Did His Time (2025)": "MVDT",

    # 2024 Teams
    "TANK BIGSBY SUPREMACY": "TBS",
    "Etienne is Butt": "EIB",
    "Sheen's Fastballs (2024)": "SF",
    "Free R. Kelly (2024)": "FRK",
    "Vancouver Gingerboogmen (2024)": "VG",
    "No Thielens": "NT",
    "Michael Vick Did His Time (2024)": "MVDT",
    "Lauderdale Muneymen 💵 (2024)": "LM",
    "No Russell Wilson? (2024)": "NRW",
    "MaLiPa Woolard": "MW",

    # 2023 Teams
    "No Russell Wilson? (2023)": "NRW",
    "Vancouver Gingerboogmen (2023)": "VG",
    "Sanduskys Daycare": "SD",
    "Pets's Xmas Carrollers": "PXC",
    "Gang Green": "GG",
    "Sheen's Fastballs (2023)": "SF",
    "Lauderdale Muneymen 💵 (2023)": "LM",
    "MaLiPa Woolard (2023)": "MW",
    "I Will Not Draft CMC Again": "IWDCMC",
    "TOP 5 TLAW (2023)": "T5",

    # 2022 Teams
    "Vancouver Gingerboogmen (2022)": "VG",
    "Sheen's Fastballs (2022)": "SF",
    "Sanduskys Daycare (2022)": "SD",
    "Boog Mansion Executive Prod": "BMEP",
    "Gang Green (2022)": "GG",
    "Lauderdale Laudy Shiners ✨": "LLS",
    "Pets's Xmas Carrollers (2022)": "PXC",
    "MaLiPa Woolard (2022)": "MW",
    "Haji's Bane Borso": "HBB",
    "Broncos Country Let's Ride": "BCLR",

    # 2021 Teams
    "Toronto Loverboys": "TLB",
    "Vancouver Gingerboogmen (2021)": "VG",
    "Yo girl Diggs me": "YGD",
    "Sanduskys Daycare (2021)": "SD",
    "Lauderdale Supreme Team": "LST",
    "Sheen's Fastballs (2021)": "SF",
    "Bruiser's Red Rocket": "BRR",
    "Team Delta": "TD",
}

# Combined mapping for backward compatibility
TEAM_ABBREVIATIONS = {**CURRENT_SEASON_TEAMS, **HISTORICAL_TEAMS}

# Reverse mapping for lookup by abbreviation
ABBREVIATIONS_TO_TEAM = {v: k for k, v in TEAM_ABBREVIATIONS.items()}

# Player/Owner first name to team mapping
PLAYER_NAMES_TO_TEAM = {
    # 2026 Teams
    "rahul": "The ChiRahuls",
    "lil": "TOP 5 TLAW",
    "canny": "TOP 5 TLAW",
    "sheen": "Sheen's Fastballs",
    "vancouver": "Vancouver Gingerboogmen",
    "vince": "Vancouver Gingerboogmen",
    "lulu": "LuLu Feet Pix II",
    "michael": "Michael Vick Did His Time",
    "vick": "Michael Vick Did His Time",
    "chinese": "Chinese Kicker",
    "kicker": "Chinese Kicker",
    "lauderdale": "Lauderdale Muneymen 💵",
    "muneymen": "Lauderdale Muneymen 💵",
    "duval": "Duval Sixers",
    "free": "Free R. Kelly",
    "kelly": "Free R. Kelly",
    "top5": "TOP 5 TLAW",
    "tlaw": "TOP 5 TLAW",

    # 2025 Teams
    "etienne": "Etienne Butt",
    "eb": "Etienne Butt",

    # 2024 Teams
    "tank": "TANK BIGSBY SUPREMACY",
    "bigsby": "TANK BIGSBY SUPREMACY",

    # 2023 Teams
    "russell": "No Russell Wilson?",
    "wilson": "No Russell Wilson?",
    "sanduskys": "Sanduskys Daycare",
    "pets": "Pets's Xmas Carrollers",
    "gang": "Gang Green",
    "malipa": "MaLiPa Woolard",

    # 2022 Teams
    "boog": "Boog Mansion Executive Prod",
    "mansion": "Boog Mansion Executive Prod",
    "haji": "Haji's Bane Borso",
    "broncos": "Broncos Country Let's Ride",

    # 2021 Teams
    "toronto": "Toronto Loverboys",
    "loverboys": "Toronto Loverboys",
    "yo": "Yo girl Diggs me",
    "diggs": "Yo girl Diggs me",
    "bruiser": "Bruiser's Red Rocket",
}

def get_abbreviation(team_name: str) -> str:
    """Get abbreviation for a team name"""
    return TEAM_ABBREVIATIONS.get(team_name, team_name[:3].upper())

def get_team_name(identifier: str) -> str:
    """Get full team name from abbreviation or player name"""
    identifier_lower = identifier.lower().strip()

    # Try exact abbreviation match first - prioritize current season (2026)
    for team_name, abbrev in CURRENT_SEASON_TEAMS.items():
        if abbrev.lower() == identifier_lower:
            return team_name

    # Then try historical years - check both with and without year suffix
    for team_name, abbrev in HISTORICAL_TEAMS.items():
        if abbrev.lower() == identifier_lower:
            # Strip year suffix (e.g., "Team Name (2025)" -> "Team Name")
            base_name = team_name.rsplit(' (', 1)[0] if ' (' in team_name else team_name
            # First check if this base name exists in current season
            for current_team in CURRENT_SEASON_TEAMS.keys():
                if current_team.lower() == base_name.lower():
                    return current_team
            # Otherwise return the historical team name
            return team_name

    # Try player/owner name match
    if identifier_lower in PLAYER_NAMES_TO_TEAM:
        team = PLAYER_NAMES_TO_TEAM[identifier_lower]
        # If it's a current season team, return it directly
        if team in CURRENT_SEASON_TEAMS:
            return team
        return team

    # Try partial player name match
    for name, team in PLAYER_NAMES_TO_TEAM.items():
        if identifier_lower in name or name in identifier_lower:
            # If it's a current season team, return it directly
            if team in CURRENT_SEASON_TEAMS:
                return team
            return team

    return None

def list_all_abbreviations() -> str:
    """Return formatted list of all team abbreviations"""
    # Get unique teams (avoid duplicates across years)
    unique_teams = {}
    for full_name, abbrev in TEAM_ABBREVIATIONS.items():
        if abbrev not in unique_teams:
            unique_teams[abbrev] = full_name

    lines = []
    for abbrev in sorted(unique_teams.keys()):
        full_name = unique_teams[abbrev]
        lines.append(f"{abbrev:<6} {full_name}")

    return "\n".join(lines)

def list_all_with_names() -> str:
    """Return formatted list with abbreviations and player names"""
    # Get unique teams
    unique_teams = {}
    for full_name, abbrev in TEAM_ABBREVIATIONS.items():
        if abbrev not in unique_teams:
            unique_teams[abbrev] = full_name

    lines = []
    for abbrev in sorted(unique_teams.keys()):
        full_name = unique_teams[abbrev]
        # Find player names for this team
        player_names = [name for name, team in PLAYER_NAMES_TO_TEAM.items() if team == full_name]
        player_str = f" ({', '.join(player_names)})" if player_names else ""
        lines.append(f"{abbrev:<6} {full_name:<40}{player_str}")

    return "\n".join(lines)


if __name__ == "__main__":
    print("Team Abbreviations & Player Names:\n")
    print(list_all_with_names())

