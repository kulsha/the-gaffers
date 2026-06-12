import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

WORLDCUP_API = "https://worldcup26.ir/get/games"
TOURNAMENT_START = "2026-06-11"

# Manual red card data — update as tournament progresses
# Key = match ID from worldcup26.ir (string)
# To add: check match result, Google red cards, add here before running
RED_CARDS_MANUAL = {
    "1": [  # Mexico 2-0 South Africa — June 11
        {"minute": 66, "team": "South Africa", "player": "S. Sithole"},
        {"minute": 84, "team": "South Africa", "player": "T. Zwane"},
        {"minute": 90, "team": "Mexico", "player": "C. Montes"}
    ],
}


def fetch_latest_match(exclude_ids: list = None):
    """
    Fetch the oldest unprocessed finished FIFA 2026 match.
    exclude_ids — list of match IDs already processed by session guard.
    """
    try:
        response = requests.get(WORLDCUP_API, timeout=10)
        response.raise_for_status()
        data = response.json()

        games = data.get("games", [])

        # Filter to only finished matches
        finished = [g for g in games if g.get("finished") == "TRUE"]

        if not finished:
            print("⚠️  No completed FIFA 2026 matches found yet.")
            print("The Gaffers will run automatically when the tournament begins on June 11.")
            return None

        # Sort ascending — process in chronological order
        finished_sorted = sorted(finished, key=lambda x: int(x["id"]))

        # Skip already processed matches
        if exclude_ids:
            finished_sorted = [
                g for g in finished_sorted
                if str(g["id"]) not in exclude_ids
            ]

        if not finished_sorted:
            return None

        # Return oldest unprocessed match
        game = finished_sorted[0]
        return parse_match(game)

    except requests.exceptions.Timeout:
        print("⚽  API request timed out. Check your connection.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API request failed: {e}")
        return None


def fetch_match_by_id(match_id: str):
    """Fetch a specific match by its ID — for testing."""
    try:
        response = requests.get(WORLDCUP_API, timeout=10)
        response.raise_for_status()
        games = response.json().get("games", [])
        for game in games:
            if str(game["id"]) == str(match_id):
                return parse_match(game)
        print(f"⚠️  Match ID {match_id} not found.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API request failed: {e}")
        return None


def parse_match(game: dict) -> dict:
    """
    Parse worldcup26.ir game object into clean match dictionary.
    """
    match_id = str(game["id"])
    home_team = game["home_team_name_en"]
    away_team = game["away_team_name_en"]
    home_score = int(game.get("home_score") or 0)
    away_score = int(game.get("away_score") or 0)

    # Parse date — format: "06/11/2026 13:00"
    raw_date = game.get("local_date", "")
    try:
        date = datetime.strptime(raw_date, "%m/%d/%Y %H:%M").strftime("%Y-%m-%d")
    except Exception:
        date = TOURNAMENT_START

    # Stage
    stage_type = game.get("type", "group")
    matchday = game.get("matchday", "1")
    group = game.get("group", "")
    if stage_type == "group":
        stage = f"Group {group} - Matchday {matchday}"
    else:
        stage = stage_type.replace("_", " ").title()

    # Parse goals from scorers string
    def parse_scorers(raw, team):
        parsed = []
        if not raw or raw == "null":
            return parsed
        clean = raw.strip('{}').replace('"', '').replace("'", "")
        for scorer in clean.split(","):
            scorer = scorer.strip()
            if not scorer:
                continue
            parts = scorer.rsplit(" ", 1)
            if len(parts) == 2:
                name = parts[0].strip()
                minute_str = parts[1].replace("'", "").strip()
                try:
                    parsed.append({
                        "minute": int(minute_str),
                        "team": team,
                        "scorer": name
                    })
                except Exception:
                    parsed.append({"minute": 0, "team": team, "scorer": scorer})
            else:
                parsed.append({"minute": 0, "team": team, "scorer": scorer})
        return parsed

    goals = []
    goals.extend(parse_scorers(game.get("home_scorers") or "", home_team))
    goals.extend(parse_scorers(game.get("away_scorers") or "", away_team))
    goals.sort(key=lambda x: x["minute"])

    # Red cards from manual data
    red_cards = RED_CARDS_MANUAL.get(match_id, [])

    # Build text
    goals_text = " | ".join([
        f"{g['scorer']} {g['minute']}' ({g['team']})"
        for g in goals
    ]) if goals else "No goals scored"

    red_cards_text = " | ".join([
        f"{r['player']} {r['minute']}' ({r['team']})"
        for r in red_cards
    ]) if red_cards else "None"

    if home_score > away_score:
        result = f"{home_team} win"
    elif away_score > home_score:
        result = f"{away_team} win"
    else:
        result = "Draw"

    # Venue from stadium_id
    stadium_map = {
        "1": "Estadio Azteca, Mexico City",
        "2": "Estadio Akron, Guadalajara",
        "3": "Estadio BBVA, Monterrey",
        "4": "AT&T Stadium, Dallas",
        "5": "NRG Stadium, Houston",
        "6": "SoFi Stadium, Los Angeles",
        "7": "Levi's Stadium, San Francisco",
        "8": "Lumen Field, Seattle",
        "9": "MetLife Stadium, New York",
        "10": "Lincoln Financial Field, Philadelphia",
        "11": "Gillette Stadium, Boston",
        "12": "Hard Rock Stadium, Miami",
        "13": "Mercedes-Benz Stadium, Atlanta",
        "14": "Arrowhead Stadium, Kansas City",
        "15": "BMO Field, Toronto",
        "16": "BC Place, Vancouver",
    }
    venue = stadium_map.get(str(game.get("stadium_id", "")), "World Cup 2026 Stadium")

    match_context = f"""
Match: {home_team} {home_score} - {away_score} {away_team}
Result: {result}
Stage: {stage}
Venue: {venue}
Date: {date}
Scorers: {goals_text}
Red Cards: {red_cards_text}
"""

    return {
        "match_id": match_id,
        "date": date,
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home_score,
        "away_score": away_score,
        "goals": goals,
        "red_cards": red_cards,
        "stage": stage,
        "venue": venue,
        "result": result,
        "match_context": match_context
    }


if __name__ == "__main__":
    print("Testing World Cup API...")
    match = fetch_latest_match()
    if match:
        print("✅ Match found:")
        print(match["match_context"])
    else:
        print("⚠️  No matches available.")