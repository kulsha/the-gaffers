import json
import os
from datetime import datetime

# Paths
DOCS_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "data")
SESSIONS_FILE = os.path.join(DOCS_DATA_DIR, "sessions.json")
AGENTS_FILE = os.path.join(DOCS_DATA_DIR, "agents.json")
MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory")

AGENT_NAMES = ["cadu", "rodrigo", "gary", "klaus", "antoine"]

COUNTRY_MAP = {
    "cadu":    {"country": "Brazil",    "flag_class": "flag-brazil",    "color": "#4ecb71"},
    "rodrigo": {"country": "Argentina", "flag_class": "flag-argentina", "color": "#74acdf"},
    "gary":    {"country": "England",   "flag_class": "flag-england",   "color": "#cf081f"},
    "klaus":   {"country": "Germany",   "flag_class": "flag-germany",   "color": "#e05252"},
    "antoine": {"country": "France",    "flag_class": "flag-france",    "color": "#0055a4"},
}

FLAG_CODES = {
    "cadu": "BRA", "rodrigo": "ARG", "gary": "ENG",
    "klaus": "GER", "antoine": "FRA"
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_session(match_data: dict, outputs: dict, session_num: int, bartender_mode: str = "silent"):
    """
    Append a new session to sessions.json.
    match_data: clean match dict from match_fetcher
    outputs: dict of agent_name -> raw response text
    session_num: sequential session number
    bartender_mode: silent / prediction / closing
    """
    sessions = load_json(SESSIONS_FILE)

    # Build conversation messages
    messages = []

    agent_order = ["cadu", "rodrigo", "gary", "klaus", "antoine"]
    for agent_name in agent_order:
        if agent_name in outputs:
            info = COUNTRY_MAP[agent_name]
            messages.append({
                "agent": agent_name,
                "name": agent_name.capitalize(),
                "flag_code": FLAG_CODES[agent_name],
                "flag_class": info["flag_class"],
                "country": info["country"],
                "country_color": info["color"],
                "text": outputs[agent_name],
                "time": datetime.now().strftime("%H:%M"),
                "is_bartender": False
            })

    # Add bartender
    if "bartender" in outputs:
        messages.append({
            "agent": "bartender",
            "name": "The Bartender",
            "flag_code": "🍺",
            "flag_class": "bartender-av",
            "country": "Neutral Zone",
            "country_color": "#d4a843",
            "text": outputs["bartender"],
            "time": datetime.now().strftime("%H:%M"),
            "is_bartender": True
        })

    # Build session object
    session = {
        "session_id": match_data["match_id"],
        "session_num": session_num,
        "date": match_data["date"],
        "day_label": _get_day_label(match_data["date"]),
        "bartender_mode": bartender_mode,
        "match": {
            "home_team": match_data["home_team"],
            "away_team": match_data["away_team"],
            "home_score": match_data["home_score"],
            "away_score": match_data["away_score"],
            "stage": match_data["stage"],
            "venue": match_data["venue"],
            "home_flag": _get_flag_for_team(match_data["home_team"]),
            "away_flag": _get_flag_for_team(match_data["away_team"]),
            "goals": match_data.get("goals", []),
            "red_cards": match_data.get("red_cards", [])
        },
        "messages": messages,
        "timestamp": datetime.now().isoformat()
    }

    sessions.append(session)
    save_json(SESSIONS_FILE, sessions)
    print(f"✅ Session {session_num:02d} saved to sessions.json")


def update_agents_json():
    """
    Refresh agents.json with current state from memory files.
    Called after every session.
    """
    agents_data = []

    for agent_name in AGENT_NAMES:
        memory_path = os.path.join(MEMORY_DIR, f"{agent_name}.json")
        try:
            memory = load_json(memory_path)
            info = COUNTRY_MAP[agent_name]

            # Calculate team record from diary
            wins = draws = losses = 0
            for entry in memory.get("tournament_diary", []):
                if entry.get("my_team_played"):
                    result = entry.get("team_result", "")
                    if result == "won":
                        wins += 1
                    elif result == "drew":
                        draws += 1
                    elif result == "lost":
                        losses += 1

            # Coming home count for Gary and Rodrigo
            coming_home = memory.get("rivalry", {}).get(
                "running_jokes", {}
            ).get("gary_coming_home_count", 0)

            agent_entry = {
                "name": agent_name.capitalize(),
                "country": info["country"],
                "flag_class": info["flag_class"],
                "flag_code": FLAG_CODES[agent_name],
                "team_status": memory.get("team_status", "active"),
                "sessions": len(memory.get("tournament_diary", [])),
                "record": f"W{wins} D{draws} L{losses}",
                "wins": wins,
                "draws": draws,
                "losses": losses,
            }

            if agent_name in ["gary", "rodrigo"]:
                agent_entry["coming_home_count"] = coming_home

            agents_data.append(agent_entry)

        except Exception as e:
            print(f"⚠️  Could not read memory for {agent_name}: {e}")

    # Add bartender
    sessions = load_json(SESSIONS_FILE)
    prediction_made = any(s.get("bartender_mode") == "prediction" for s in sessions)
    agents_data.append({
        "name": "The Bartender",
        "country": "Neutral Zone",
        "flag_class": "bartender",
        "flag_code": "🍺",
        "team_status": "observing",
        "sessions": len(sessions),
        "prediction_made": prediction_made
    })

    save_json(AGENTS_FILE, agents_data)
    print(f"✅ agents.json updated — {len(agents_data)} agents")


def _get_day_label(date_str: str) -> str:
    tournament_start = datetime(2026, 6, 11)
    match_date = datetime.strptime(date_str, "%Y-%m-%d")
    day_num = (match_date - tournament_start).days + 1
    month_name = match_date.strftime("%B %d").lstrip("0")
    return f"Day {day_num} · {month_name}"


def _get_flag_for_team(team_name: str) -> dict:
    team_flags = {
        "Brazil":      {"code": "BRA", "style": "background:linear-gradient(135deg,#009c3b,#FFDF00)"},
        "Argentina":   {"code": "ARG", "style": "background:linear-gradient(135deg,#4fa8d8,#ffffff)"},
        "England":     {"code": "ENG", "style": "background:#cf081f"},
        "Germany":     {"code": "GER", "style": "background:linear-gradient(180deg,#1a1a1a,#dd0000,#FFCE00)"},
        "France":      {"code": "FRA", "style": "background:linear-gradient(90deg,#002395 33%,#ffffff 33%,#ffffff 66%,#ED2939 66%)"},
        "Mexico":      {"code": "MEX", "style": "background:linear-gradient(135deg,#006847,#CE1126)"},
        "Morocco":     {"code": "MAR", "style": "background:linear-gradient(135deg,#006233,#C1272D)"},
        "Croatia":     {"code": "CRO", "style": "background:linear-gradient(135deg,#FF0000,#ffffff,#0000CD)"},
        "Serbia":      {"code": "SRB", "style": "background:linear-gradient(135deg,#C6363C,#0C4076)"},
        "Poland":      {"code": "POL", "style": "background:linear-gradient(135deg,#DC143C,#ffffff)"},
        "Portugal":    {"code": "POR", "style": "background:linear-gradient(135deg,#006600,#FF0000)"},
        "Spain":       {"code": "ESP", "style": "background:linear-gradient(135deg,#AA151B,#F1BF00)"},
        "Netherlands": {"code": "NED", "style": "background:linear-gradient(180deg,#AE1C28,#ffffff,#21468B)"},
        "USA":         {"code": "USA", "style": "background:linear-gradient(135deg,#002868,#BF0A30)"},
        "Canada":      {"code": "CAN", "style": "background:linear-gradient(135deg,#FF0000,#ffffff)"},
        "Japan":       {"code": "JPN", "style": "background:radial-gradient(circle,#BC002D 40%,#ffffff 40%)"},
        "South Korea": {"code": "KOR", "style": "background:linear-gradient(135deg,#CD2E3A,#0047A0)"},
        "Australia":   {"code": "AUS", "style": "background:linear-gradient(135deg,#00008B,#FF0000)"},
        "Ecuador":     {"code": "ECU", "style": "background:linear-gradient(180deg,#FFD100,#003DA5,#EF3340)"},
        "Uruguay":     {"code": "URU", "style": "background:linear-gradient(135deg,#5EB6E4,#ffffff)"},
        "Colombia":    {"code": "COL", "style": "background:linear-gradient(180deg,#FCD116,#003087,#CE1126)"},
        "Senegal":     {"code": "SEN", "style": "background:linear-gradient(90deg,#00853F,#FDEF42,#E31B23)"},
        "Ghana":       {"code": "GHA", "style": "background:linear-gradient(180deg,#006B3F,#FCD116,#CE1126)"},
        "Nigeria":     {"code": "NGA", "style": "background:linear-gradient(90deg,#008751,#ffffff,#008751)"},
        "South Africa":{"code": "RSA", "style": "background:linear-gradient(135deg,#007A4D,#FFB612,#DE3831)"},
        "Haiti":       {"code": "HAI", "style": "background:linear-gradient(180deg,#00209F,#D21034)"},
        "Scotland":    {"code": "SCO", "style": "background:linear-gradient(135deg,#003078,#ffffff)"},
        "Switzerland": {"code": "SUI", "style": "background:linear-gradient(135deg,#FF0000,#ffffff)"},
        "Qatar":       {"code": "QAT", "style": "background:linear-gradient(135deg,#8D1B3D,#ffffff)"},
        "Paraguay":    {"code": "PAR", "style": "background:linear-gradient(180deg,#D52B1E,#ffffff,#009B3A)"},
        "Austria":     {"code": "AUT", "style": "background:linear-gradient(180deg,#ED2939,#ffffff,#ED2939)"},
        "Jordan":      {"code": "JOR", "style": "background:linear-gradient(180deg,#007A3D,#ffffff,#CE1126)"},
        "Algeria":     {"code": "ALG", "style": "background:linear-gradient(90deg,#006233,#ffffff,#D21034)"},
        "Ukraine":     {"code": "UKR", "style": "background:linear-gradient(180deg,#005BBB,#FFD500)"},
        "Belgium":     {"code": "BEL", "style": "background:linear-gradient(90deg,#000000,#FFD90C,#F31830)"},
        "Czech Republic":{"code":"CZE","style":"background:linear-gradient(180deg,#D7141A,#ffffff)"},
        "Norway":      {"code": "NOR", "style": "background:linear-gradient(135deg,#EF2B2D,#002868)"},
        "Curacao":     {"code": "CUW", "style": "background:linear-gradient(135deg,#003DA5,#F9E300)"},
        "Saudi Arabia":{"code":"KSA","style":"background:linear-gradient(135deg,#006C35,#ffffff)"},
        "Cape Verde":  {"code":"CPV","style":"background:linear-gradient(135deg,#003893,#CF2027)"},
        "Uzbekistan":  {"code":"UZB","style":"background:linear-gradient(180deg,#1EB53A,#ffffff,#009FCA)"},
        "Bosnia and Herzegovina":{"code":"BIH","style":"background:linear-gradient(135deg,#002395,#FFCD00)"},
        "Czechia":     {"code":"CZE","style":"background:linear-gradient(180deg,#D7141A,#ffffff)"},
    }

    if team_name in team_flags:
        return team_flags[team_name]
    else:
        initials = "".join([w[0] for w in team_name.split()[:3]]).upper()
        return {
            "code": initials,
            "style": "background:linear-gradient(135deg,#333355,#555577)"
        }