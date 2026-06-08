import os
import subprocess
import json
from datetime import datetime
from utils.html_generator import add_session, update_agents_json

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
SESSIONS_FILE = os.path.join(DOCS_DIR, "data", "sessions.json")


def update_site(match_data: dict, outputs: dict, session_num: int, bartender_mode: str = "silent"):
    """
    Full site update after every session.
    1. Add session to sessions.json
    2. Update agents.json
    3. Git commit and push
    """
    print("\n🌐 Updating website...")

    # Step 1 — Add session with bartender_mode
    add_session(match_data, outputs, session_num, bartender_mode)

    # Step 2 — Update agent cards
    update_agents_json()

    # Step 3 — Git commit and push
    _git_push(match_data, session_num)

    print("✅ Website updated and pushed to GitHub Pages")


def _git_push(match_data: dict, session_num: int):
    commit_message = (
        f"session {session_num:03d}: "
        f"{match_data['home_team']} {match_data['home_score']}-"
        f"{match_data['away_score']} {match_data['away_team']} "
        f"· {match_data['date']}"
    )

    try:
        subprocess.run(
            ["git", "add", "docs/data/sessions.json", "docs/data/agents.json", "memory/"],
            cwd=PROJECT_ROOT, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=PROJECT_ROOT, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=PROJECT_ROOT, check=True, capture_output=True
        )
        print(f"📤 Pushed: {commit_message}")

    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git push failed: {e}")
        print("Sessions saved locally — push manually when ready.")


def get_tournament_stats() -> dict:
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            sessions = json.load(f)
        total_sessions = len(sessions)
        dates = list(set(s["date"] for s in sessions))
        days_active = len(dates)
        return {
            "total_sessions": total_sessions,
            "days_active": days_active,
            "latest_session": sessions[-1] if sessions else None
        }
    except Exception:
        return {"total_sessions": 0, "days_active": 0, "latest_session": None}


def get_sessions_by_day() -> dict:
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            sessions = json.load(f)
        by_day = {}
        for session in sessions:
            date = session["date"]
            if date not in by_day:
                by_day[date] = []
            by_day[date].append(session)
        return by_day
    except Exception:
        return {}