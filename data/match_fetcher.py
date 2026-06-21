import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

WORLDCUP_API = "https://worldcup26.ir/get/games"
TOURNAMENT_START = "2026-06-11"

# Manual red card data — update as tournament progresses
# Key = match ID from worldcup26.ir (string)
RED_CARDS_MANUAL = {
    "1": [  # Mexico 2-0 South Africa — June 11
        {"minute": 66, "team": "South Africa", "player": "S. Sithole"},
        {"minute": 84, "team": "South Africa", "player": "T. Zwane"},
        {"minute": 90, "team": "Mexico", "player": "C. Montes"}
    ],
    "25": [  # Czechia vs South Africa
        # no red cards
    ],
    "26": [  # Switzerland 4-1 Bosnia
        {"minute": 78, "team": "Bosnia and Herzegovina", "player": "T. Muharemović"}
    ],
    "27": [  # Canada 6-0 Qatar
        {"minute": 62, "team": "Qatar", "player": "H. Ahmed"},
        {"minute": 75, "team": "Qatar", "player": "A. Madibo"}
    ],
    "32": [  # Turkey 0-1 Paraguay
        {"minute": 45, "team": "Turkey", "player": "M. Almirón"}
    ],
}

# Manual fallback — used when worldcup26.ir is down
# Set to [] when API is back up — system switches to live data automatically
MANUAL_FALLBACK = [
    {   # Session 17 — France 3-1 Senegal
        "id": "17",
        "home_team_name_en": "France",
        "away_team_name_en": "Senegal",
        "home_score": "3",
        "away_score": "1",
        "home_scorers": '{"K. Mbappé 66\'","B. Barcola 82\'","K. Mbappé 95\'"}',
        "away_scorers": '{"I. Mbaye 93\'"}',
        "group": "I",
        "matchday": "1",
        "local_date": "06/16/2026 15:00",
        "stadium_id": "11",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 18 — Norway 4-1 Iraq
        "id": "18",
        "home_team_name_en": "Norway",
        "away_team_name_en": "Iraq",
        "home_score": "4",
        "away_score": "1",
        "home_scorers": '{"E. Haaland 29\'","E. Haaland 43\'","L. Østigård 78\'","K. Thorstvedt 89\'"}',
        "away_scorers": '{"A. Hussein 39\'"}',
        "group": "I",
        "matchday": "1",
        "local_date": "06/16/2026 18:00",
        "stadium_id": "9",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 19 — Argentina 3-0 Algeria
        "id": "19",
        "home_team_name_en": "Argentina",
        "away_team_name_en": "Algeria",
        "home_score": "3",
        "away_score": "0",
        "home_scorers": '{"L. Messi 12\'","L. Messi 45\'","L. Messi 61\'"}',
        "away_scorers": "null",
        "group": "J",
        "matchday": "1",
        "local_date": "06/16/2026 20:00",
        "stadium_id": "7",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 20 — Austria 3-1 Jordan
        "id": "20",
        "home_team_name_en": "Austria",
        "away_team_name_en": "Jordan",
        "home_score": "3",
        "away_score": "1",
        "home_scorers": '{"R. Schmid 21\'","Y. Al-Arab 76\' OG","M. Arnautovic 90\'"}',
        "away_scorers": '{"A. Olwan 50\'"}',
        "group": "J",
        "matchday": "1",
        "local_date": "06/16/2026 21:00",
        "stadium_id": "6",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 21 — Portugal 1-1 DR Congo
        "id": "21",
        "home_team_name_en": "Portugal",
        "away_team_name_en": "DR Congo",
        "home_score": "1",
        "away_score": "1",
        "home_scorers": '{"J. Neves 6\'"}',
        "away_scorers": '{"Y. Wissa 45\'"}',
        "group": "K",
        "matchday": "1",
        "local_date": "06/17/2026 13:00",
        "stadium_id": "5",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 22 — England 4-2 Croatia
        "id": "22",
        "home_team_name_en": "England",
        "away_team_name_en": "Croatia",
        "home_score": "4",
        "away_score": "2",
        "home_scorers": '{"H. Kane 22\'","H. Kane 54\'","J. Bellingham 67\'","M. Rashford 78\'"}',
        "away_scorers": '{"P. Musa 35\'","I. Perišić 49\'"}',
        "group": "L",
        "matchday": "1",
        "local_date": "06/17/2026 17:00",
        "stadium_id": "4",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 23 — Ghana 1-0 Panama
        "id": "23",
        "home_team_name_en": "Ghana",
        "away_team_name_en": "Panama",
        "home_score": "1",
        "away_score": "0",
        "home_scorers": '{"C. Yirenkyi 95\'"}',
        "away_scorers": "null",
        "group": "L",
        "matchday": "1",
        "local_date": "06/17/2026 19:00",
        "stadium_id": "12",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 24 — Colombia 3-1 Uzbekistan
        "id": "24",
        "home_team_name_en": "Colombia",
        "away_team_name_en": "Uzbekistan",
        "home_score": "3",
        "away_score": "1",
        "home_scorers": '{"D. Muñoz 40\'","L. Díaz 55\'","J. Campaz 90\'"}',
        "away_scorers": '{"A. Fayzullaev 50\'"}',
        "group": "K",
        "matchday": "1",
        "local_date": "06/17/2026 22:00",
        "stadium_id": "2",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 25 — Czechia 1-1 South Africa
        "id": "25",
        "home_team_name_en": "Czechia",
        "away_team_name_en": "South Africa",
        "home_score": "1",
        "away_score": "1",
        "home_scorers": '{"M. Sadílek 6\'"}',
        "away_scorers": '{"T. Mokoena 83\' pen"}',
        "group": "A",
        "matchday": "2",
        "local_date": "06/18/2026 05:00",
        "stadium_id": "13",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 26 — Switzerland 4-1 Bosnia
        "id": "26",
        "home_team_name_en": "Switzerland",
        "away_team_name_en": "Bosnia and Herzegovina",
        "home_score": "4",
        "away_score": "1",
        "home_scorers": '{"J. Manzambi 74\'","R. Vargas 79\'","J. Manzambi 90\'","G. Xhaka 90\' pen"}',
        "away_scorers": '{"E. Mahmić 88\'"}',
        "group": "B",
        "matchday": "2",
        "local_date": "06/18/2026 08:00",
        "stadium_id": "16",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 27 — Canada 6-0 Qatar
        "id": "27",
        "home_team_name_en": "Canada",
        "away_team_name_en": "Qatar",
        "home_score": "6",
        "away_score": "0",
        "home_scorers": '{"C. Larin 18\'","J. David 34\'","J. David 45\'","N. Saliba 68\'","M. Al Mannai 77\' OG","J. David 85\'"}',
        "away_scorers": "null",
        "group": "B",
        "matchday": "2",
        "local_date": "06/18/2026 11:00",
        "stadium_id": "13",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 28 — Mexico 1-0 South Korea
        "id": "28",
        "home_team_name_en": "Mexico",
        "away_team_name_en": "South Korea",
        "home_score": "1",
        "away_score": "0",
        "home_scorers": '{"L. Romo 58\'"}',
        "away_scorers": "null",
        "group": "A",
        "matchday": "2",
        "local_date": "06/18/2026 14:00",
        "stadium_id": "2",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 29 — USA 2-0 Australia
        "id": "29",
        "home_team_name_en": "United States",
        "away_team_name_en": "Australia",
        "home_score": "2",
        "away_score": "0",
        "home_scorers": '{"C. Burgess 12\' OG","A. Freeman 38\'"}',
        "away_scorers": "null",
        "group": "D",
        "matchday": "2",
        "local_date": "06/19/2026 09:00",
        "stadium_id": "8",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 30 — Morocco 1-0 Scotland
        "id": "30",
        "home_team_name_en": "Morocco",
        "away_team_name_en": "Scotland",
        "home_score": "1",
        "away_score": "0",
        "home_scorers": '{"I. Saibari 1\'"}',
        "away_scorers": "null",
        "group": "C",
        "matchday": "2",
        "local_date": "06/19/2026 12:00",
        "stadium_id": "9",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 31 — Brazil 3-0 Haiti
        "id": "31",
        "home_team_name_en": "Brazil",
        "away_team_name_en": "Haiti",
        "home_score": "3",
        "away_score": "0",
        "home_scorers": '{"M. Cunha 22\'","V. Júnior 45\'","M. Cunha 67\'"}',
        "away_scorers": "null",
        "group": "C",
        "matchday": "2",
        "local_date": "06/19/2026 15:00",
        "stadium_id": "10",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 32 — Turkey 0-1 Paraguay
        "id": "32",
        "home_team_name_en": "Turkey",
        "away_team_name_en": "Paraguay",
        "home_score": "0",
        "away_score": "1",
        "home_scorers": "null",
        "away_scorers": '{"M. Galarza 1\'"}',
        "group": "D",
        "matchday": "2",
        "local_date": "06/19/2026 18:00",
        "stadium_id": "6",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 33 — Netherlands 5-1 Sweden
        "id": "33",
        "home_team_name_en": "Netherlands",
        "away_team_name_en": "Sweden",
        "home_score": "5",
        "away_score": "1",
        "home_scorers": '{"B. Brobbey 8\'","B. Brobbey 23\'","C. Gakpo 52\'","C. Gakpo 58\'","C. Summerville 78\'"}',
        "away_scorers": '{"A. Elanga 71\'"}',
        "group": "F",
        "matchday": "2",
        "local_date": "06/20/2026 09:00",
        "stadium_id": "5",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 34 — Germany 2-1 Ivory Coast
        "id": "34",
        "home_team_name_en": "Germany",
        "away_team_name_en": "Ivory Coast",
        "home_score": "2",
        "away_score": "1",
        "home_scorers": '{"D. Undav 68\'","D. Undav 90\'"}',
        "away_scorers": '{"F. Kessié 34\'"}',
        "group": "E",
        "matchday": "2",
        "local_date": "06/20/2026 09:00",
        "stadium_id": "12",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 35 — Ecuador 0-0 Curaçao
        "id": "35",
        "home_team_name_en": "Ecuador",
        "away_team_name_en": "Curacao",
        "home_score": "0",
        "away_score": "0",
        "home_scorers": "null",
        "away_scorers": "null",
        "group": "E",
        "matchday": "2",
        "local_date": "06/20/2026 09:00",
        "stadium_id": "7",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
    {   # Session 36 — Tunisia 0-4 Japan
        "id": "36",
        "home_team_name_en": "Tunisia",
        "away_team_name_en": "Japan",
        "home_score": "0",
        "away_score": "4",
        "home_scorers": "null",
        "away_scorers": '{"D. Kamada 4\'","A. Ueda 31\'","J. Ito 69\'","A. Ueda 83\'"}',
        "group": "F",
        "matchday": "2",
        "local_date": "06/20/2026 22:00",
        "stadium_id": "3",
        "finished": "TRUE",
        "time_elapsed": "finished",
        "type": "group"
    },
]


# Match-specific venue map — covers all 104 matches
MATCH_VENUE_MAP = {
    "1":   "Estadio Azteca, Mexico City",
    "2":   "Estadio Akron, Zapopan",
    "3":   "BMO Field, Toronto",
    "4":   "SoFi Stadium, Inglewood",
    "5":   "Levi's Stadium, Santa Clara",
    "6":   "MetLife Stadium, East Rutherford",
    "7":   "Gillette Stadium, Foxborough",
    "8":   "BC Place, Vancouver",
    "9":   "NRG Stadium, Houston",
    "10":  "AT&T Stadium, Arlington",
    "11":  "Lincoln Financial Field, Philadelphia",
    "12":  "Estadio BBVA, Monterrey",
    "13":  "Mercedes-Benz Stadium, Atlanta",
    "14":  "Lumen Field, Seattle",
    "15":  "Hard Rock Stadium, Miami Gardens",
    "16":  "SoFi Stadium, Inglewood",
    "17":  "MetLife Stadium, East Rutherford",
    "18":  "Gillette Stadium, Foxborough",
    "19":  "Arrowhead Stadium, Kansas City",
    "20":  "Levi's Stadium, Santa Clara",
    "21":  "NRG Stadium, Houston",
    "22":  "AT&T Stadium, Arlington",
    "23":  "BMO Field, Toronto",
    "24":  "Estadio Azteca, Mexico City",
    "25":  "Mercedes-Benz Stadium, Atlanta",
    "26":  "SoFi Stadium, Inglewood",
    "27":  "BC Place, Vancouver",
    "28":  "Estadio Akron, Zapopan",
    "29":  "Lumen Field, Seattle",
    "30":  "Gillette Stadium, Foxborough",
    "31":  "Lincoln Financial Field, Philadelphia",
    "32":  "Levi's Stadium, Santa Clara",
    "33":  "NRG Stadium, Houston",
    "34":  "BMO Field, Toronto",
    "35":  "Arrowhead Stadium, Kansas City",
    "36":  "Estadio BBVA, Monterrey",
    "37":  "Mercedes-Benz Stadium, Atlanta",
    "38":  "SoFi Stadium, Inglewood",
    "39":  "Hard Rock Stadium, Miami Gardens",
    "40":  "BC Place, Vancouver",
    "41":  "AT&T Stadium, Arlington",
    "42":  "Lincoln Financial Field, Philadelphia",
    "43":  "MetLife Stadium, East Rutherford",
    "44":  "Levi's Stadium, Santa Clara",
    "45":  "NRG Stadium, Houston",
    "46":  "Gillette Stadium, Foxborough",
    "47":  "BMO Field, Toronto",
    "48":  "Estadio Akron, Zapopan",
    "49":  "BC Place, Vancouver",
    "50":  "Lumen Field, Seattle",
    "51":  "Hard Rock Stadium, Miami Gardens",
    "52":  "Mercedes-Benz Stadium, Atlanta",
    "53":  "Estadio Azteca, Mexico City",
    "54":  "Estadio BBVA, Monterrey",
    "55":  "Lincoln Financial Field, Philadelphia",
    "56":  "MetLife Stadium, East Rutherford",
    "57":  "AT&T Stadium, Arlington",
    "58":  "Arrowhead Stadium, Kansas City",
    "59":  "SoFi Stadium, Inglewood",
    "60":  "Levi's Stadium, Santa Clara",
    "61":  "Gillette Stadium, Foxborough",
    "62":  "BMO Field, Toronto",
    "63":  "NRG Stadium, Houston",
    "64":  "Estadio Akron, Zapopan",
    "65":  "Lumen Field, Seattle",
    "66":  "BC Place, Vancouver",
    "67":  "MetLife Stadium, East Rutherford",
    "68":  "Lincoln Financial Field, Philadelphia",
    "69":  "Hard Rock Stadium, Miami Gardens",
    "70":  "Mercedes-Benz Stadium, Atlanta",
    "71":  "Arrowhead Stadium, Kansas City",
    "72":  "AT&T Stadium, Arlington",
    "73":  "SoFi Stadium, Inglewood",
    "74":  "NRG Stadium, Houston",
    "75":  "Gillette Stadium, Foxborough",
    "76":  "Estadio BBVA, Monterrey",
    "77":  "AT&T Stadium, Arlington",
    "78":  "MetLife Stadium, East Rutherford",
    "79":  "Estadio Azteca, Mexico City",
    "80":  "Mercedes-Benz Stadium, Atlanta",
    "81":  "Lumen Field, Seattle",
    "82":  "Levi's Stadium, Santa Clara",
    "83":  "SoFi Stadium, Inglewood",
    "84":  "BMO Field, Toronto",
    "85":  "BC Place, Vancouver",
    "86":  "AT&T Stadium, Arlington",
    "87":  "Hard Rock Stadium, Miami Gardens",
    "88":  "Arrowhead Stadium, Kansas City",
    "89":  "NRG Stadium, Houston",
    "90":  "Lincoln Financial Field, Philadelphia",
    "91":  "MetLife Stadium, East Rutherford",
    "92":  "Estadio Azteca, Mexico City",
    "93":  "AT&T Stadium, Arlington",
    "94":  "Lumen Field, Seattle",
    "95":  "Mercedes-Benz Stadium, Atlanta",
    "96":  "BC Place, Vancouver",
    "97":  "Gillette Stadium, Foxborough",
    "98":  "SoFi Stadium, Inglewood",
    "99":  "Hard Rock Stadium, Miami Gardens",
    "100": "Arrowhead Stadium, Kansas City",
    "101": "AT&T Stadium, Arlington",
    "102": "Mercedes-Benz Stadium, Atlanta",
    "103": "Hard Rock Stadium, Miami Gardens",
    "104": "MetLife Stadium, East Rutherford",
}


def fetch_latest_match(exclude_ids: list = None):
    """
    Fetch the oldest unprocessed finished FIFA 2026 match.
    Tries API first — uses MANUAL_FALLBACK only if API fails.
    exclude_ids — list of match IDs already processed by session guard.
    """
    games = []

    if MANUAL_FALLBACK:
        # Try API first even when fallback is populated
        try:
            response = requests.get(WORLDCUP_API, timeout=10)
            response.raise_for_status()
            api_games = response.json().get("games", [])
            if api_games:
                print("✅ API is back up — using live data.")
                games = api_games
            else:
                print("⚠️  API returned empty — using manual fallback.")
                games = MANUAL_FALLBACK
        except Exception:
            print("⚠️  API unavailable — using manual fallback data.")
            games = MANUAL_FALLBACK
    else:
        try:
            response = requests.get(WORLDCUP_API, timeout=10)
            response.raise_for_status()
            games = response.json().get("games", [])
        except requests.exceptions.Timeout:
            print("⚠️  API request timed out. Check your connection.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"⚠️  API request failed: {e}")
            return None

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

    # Venue from match-specific map
    venue = MATCH_VENUE_MAP.get(match_id, "World Cup 2026 Stadium")

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