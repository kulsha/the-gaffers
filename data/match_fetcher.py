import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
FIFA_LEAGUE_ID = 1
FIFA_SEASON = 2026


def fetch_latest_match():
    """
    Fetch the most recently completed FIFA 2026 match.
    Returns a clean match dictionary or None if no match found.
    """
    headers = {
        "x-apisports-key": API_KEY
    }

    params = {
        "league": FIFA_LEAGUE_ID,
        "season": FIFA_SEASON,
        "last": 1,
        "status": "FT"
    }

    try:
        response = requests.get(
            f"{BASE_URL}/fixtures",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data["response"]:
            print("⚠️  No completed FIFA 2026 matches found yet.")
            print("The Gaffers will run automatically when the tournament begins on June 11.")
            return None

        fixture = data["response"][0]
        return parse_match(fixture)

    except requests.exceptions.Timeout:
        print("⚠️  API request timed out. Check your connection.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API request failed: {e}")
        return None


def fetch_match_by_id(fixture_id: int):
    """
    Fetch a specific match by its fixture ID.
    Useful for testing with a known past match.
    """
    headers = {
        "x-apisports-key": API_KEY
    }

    params = {
        "id": fixture_id
    }

    try:
        response = requests.get(
            f"{BASE_URL}/fixtures",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data["response"]:
            print(f"⚠️  No match found for fixture ID {fixture_id}")
            return None

        fixture = data["response"][0]
        return parse_match(fixture)

    except requests.exceptions.RequestException as e:
        print(f"⚠️  API request failed: {e}")
        return None


def parse_match(fixture: dict) -> dict:
    """
    Parse raw API response into clean match dictionary.
    This is what gets fed into agent prompts.
    """
    match_id = str(fixture["fixture"]["id"])
    date = fixture["fixture"]["date"][:10]
    venue = fixture["fixture"]["venue"]["name"]
    city = fixture["fixture"]["venue"]["city"]
    stage = fixture["league"]["round"]

    home_team = fixture["teams"]["home"]["name"]
    away_team = fixture["teams"]["away"]["name"]
    home_score = fixture["goals"]["home"]
    away_score = fixture["goals"]["away"]

    goals = []
    if fixture.get("events"):
        for event in fixture["events"]:
            if event["type"] == "Goal":
                goals.append({
                    "minute": event["time"]["elapsed"],
                    "team": event["team"]["name"],
                    "scorer": event["player"]["name"]
                })

    red_cards = []
    if fixture.get("events"):
        for event in fixture["events"]:
            if event["type"] == "Card" and event["detail"] == "Red Card":
                red_cards.append({
                    "minute": event["time"]["elapsed"],
                    "team": event["team"]["name"],
                    "player": event["player"]["name"]
                })

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

    match_context = f"""
Match: {home_team} {home_score} - {away_score} {away_team}
Result: {result}
Stage: {stage}
Venue: {venue}, {city}
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
        "venue": f"{venue}, {city}",
        "result": result,
        "match_context": match_context
    }


if __name__ == "__main__":
    print("Testing API connection...")
    match = fetch_latest_match()

    if match:
        print("✅ Live match found:")
        print(match["match_context"])
    else:
        print("⚠️  No FIFA 2026 matches available yet.")
        print("The Gaffers will run automatically when the tournament begins on June 11.")