import os
import sys
from dotenv import load_dotenv
from crewai import Crew, Task, Process

from agents.cadu import create_cadu
from agents.rodrigo import create_rodrigo
from agents.gary import create_gary
from agents.klaus import create_klaus
from agents.antoine import create_antoine
from agents.bartender import create_bartender
from data.match_fetcher import fetch_latest_match
from utils.session_guard import (
    already_ran,
    mark_session_complete,
    update_reaction_summary,
    get_session_count,
    should_bartender_predict,
    should_bartender_close
)
from utils.memory_manager import update_mood, increment_rivalry_count
from utils.site_updater import update_site

load_dotenv()

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"


def calculate_mood_deltas(agent_name: str, match_data: dict) -> dict:
    country_map = {
        "cadu":    "Brazil",
        "rodrigo": "Argentina",
        "gary":    "England",
        "klaus":   "Germany",
        "antoine": "France"
    }

    agent_country = country_map[agent_name]
    home = match_data["home_team"]
    away = match_data["away_team"]
    result = match_data["result"]

    my_team_played = agent_country in [home, away]

    if my_team_played:
        my_team_won = result == f"{agent_country} win"
        my_team_drew = result == "Draw"

        if my_team_won:
            return {"hope": +10, "confidence": +8, "anger": -5, "bitterness": -3}
        elif my_team_drew:
            return {"hope": -5, "confidence": -3, "anger": +5, "bitterness": +3}
        else:
            return {"hope": -15, "confidence": -10, "anger": +20, "bitterness": +12}
    else:
        rival_map = {
            "cadu":    ["Argentina"],
            "rodrigo": ["Brazil", "England"],
            "gary":    ["Argentina", "France"],
            "klaus":   ["Brazil"],
            "antoine": ["England", "Germany"]
        }

        rivals = rival_map.get(agent_name, [])
        rival_won = any(
            result == f"{r} win" for r in rivals
            if r in [home, away]
        )

        if rival_won:
            return {"hope": -3, "anger": +8, "bitterness": +5, "confidence": -2}
        else:
            return {"hope": +2, "anger": -2, "bitterness": -1, "confidence": +1}


def print_session_header(match_data: dict, session_num: int):
    print("\n" + "="*55)
    print("  THE NEUTRAL ZONE · New York")
    print("  FIFA World Cup 2026")
    print(f"  Session {session_num:02d} · {match_data['date']}")
    print(f"  {match_data['home_team']} {match_data['home_score']} - {match_data['away_score']} {match_data['away_team']}")
    print(f"  {match_data['stage']} · {match_data['venue']}")
    print("="*55 + "\n")


def run_crew(match_context: str, bartender_mode: str):
    """
    Build agents, tasks and run the crew.
    Returns outputs dict.
    """
    cadu    = create_cadu(match_context)
    rodrigo = create_rodrigo(match_context)
    gary    = create_gary(match_context)
    klaus   = create_klaus(match_context)
    antoine = create_antoine(match_context)
    bartender = create_bartender(mode=bartender_mode)

    task_cadu = Task(
        description=f"""
        The match just finished: {match_context}
        You are sitting in The Neutral Zone sports bar in New York.
        React to this result. Be Cadu. 2-4 sentences maximum.
        """,
        expected_output="A raw emotional reaction in Cadu's voice",
        agent=cadu
    )
    task_rodrigo = Task(
        description=f"""
        The match just finished: {match_context}
        Cadu just reacted. You heard what he said.
        React to the match AND respond to Cadu if relevant.
        Be Rodrigo. 2-4 sentences maximum.
        """,
        expected_output="Rodrigo's reaction to the match and possibly Cadu",
        agent=rodrigo,
        context=[task_cadu]
    )
    task_gary = Task(
        description=f"""
        The match just finished: {match_context}
        Cadu and Rodrigo have both spoken. You heard everything.
        React to the match. Respond to anyone if relevant.
        Be Gary. 2-4 sentences maximum.
        """,
        expected_output="Gary's reaction to the match and conversation so far",
        agent=gary,
        context=[task_cadu, task_rodrigo]
    )
    task_klaus = Task(
        description=f"""
        The match just finished: {match_context}
        Cadu, Rodrigo and Gary have all reacted. You heard everything.
        React with analysis. Correct anyone if their reasoning is wrong.
        Be Klaus. 2-4 sentences maximum.
        """,
        expected_output="Klaus's analytical reaction with at least one statistic",
        agent=klaus,
        context=[task_cadu, task_rodrigo, task_gary]
    )
    task_antoine = Task(
        description=f"""
        The match just finished: {match_context}
        Everyone has spoken. You have heard it all.
        React philosophically. Respond to whoever said something worth responding to.
        Be Antoine. 2-4 sentences maximum.
        """,
        expected_output="Antoine's philosophical calm reaction",
        agent=antoine,
        context=[task_cadu, task_rodrigo, task_gary, task_klaus]
    )
    task_bartender = Task(
        description=f"""
        You have watched the whole session tonight.
        Five fans reacted to: {match_context}
        End the session in your mode: {bartender_mode}
        """,
        expected_output="The bartender's closing for tonight",
        agent=bartender,
        context=[task_cadu, task_rodrigo, task_gary, task_klaus, task_antoine]
    )

    crew = Crew(
        agents=[cadu, rodrigo, gary, klaus, antoine, bartender],
        tasks=[task_cadu, task_rodrigo, task_gary, task_klaus, task_antoine, task_bartender],
        process=Process.sequential,
        verbose=False
    )

    crew.kickoff()

    return {
        "cadu":      task_cadu.output.raw if task_cadu.output else "...",
        "rodrigo":   task_rodrigo.output.raw if task_rodrigo.output else "...",
        "gary":      task_gary.output.raw if task_gary.output else "...",
        "klaus":     task_klaus.output.raw if task_klaus.output else "...",
        "antoine":   task_antoine.output.raw if task_antoine.output else "...",
        "bartender": task_bartender.output.raw if task_bartender.output else "..."
    }


def print_outputs(outputs: dict):
    print("\n🇧🇷 CADU");         print(outputs["cadu"])
    print("\n🇦🇷 RODRIGO");      print(outputs["rodrigo"])
    print("\n🏴󠁧󠁢󠁥󠁬󠁧󠁿 GARY");        print(outputs["gary"])
    print("\n🇩🇪 KLAUS");        print(outputs["klaus"])
    print("\n🇫🇷 ANTOINE");      print(outputs["antoine"])
    print("\n🍺 THE BARTENDER"); print(outputs["bartender"])
    print("\n" + "="*55 + "\n")


def update_memories(match_data: dict, outputs: dict, match_id: str):
    """Update all agent memories after a session."""
    agent_names = ["cadu", "rodrigo", "gary", "klaus", "antoine"]

    mark_session_complete(match_id, match_data)

    for agent_name in agent_names:
        update_reaction_summary(agent_name, match_id, outputs[agent_name][:150])

    for agent_name in agent_names:
        deltas = calculate_mood_deltas(agent_name, match_data)
        update_mood(agent_name, deltas)

    gary_output = outputs["gary"].lower()
    if "coming home" in gary_output or "football's coming" in gary_output:
        for agent_name in agent_names:
            increment_rivalry_count(agent_name, "gary_coming_home_count")
        print("⚽ Gary said it again. Count updated.")

    print("✅ Memories updated.")


def run_session():
    """
    Main session runner — uses live FIFA 2026 API data.
    This runs autonomously from June 11 onwards.
    """

    # ── Step 1 — Fetch latest match ──
    print("\n⚽ Fetching latest FIFA 2026 match...")
    match_data = fetch_latest_match()

    if not match_data:
        print("⚠️  No FIFA 2026 match available.")
        print("Come back after the next match finishes.")
        sys.exit(0)

    match_id = match_data["match_id"]
    match_context = match_data["match_context"]

    # ── Step 2 — Session guard ──
    if already_ran(match_id):
        print(f"⚠️  Session already ran for this match.")
        print(f"Match: {match_data['home_team']} vs {match_data['away_team']}")
        print("Come back after the next match.")
        sys.exit(0)

    # ── Step 3 — Session header ──
    session_num = get_session_count() + 1
    print_session_header(match_data, session_num)

    # ── Step 4 — Bartender mode ──
    if should_bartender_close():
        bartender_mode = "closing"
    elif should_bartender_predict():
        bartender_mode = "prediction"
    else:
        bartender_mode = "silent"

    # ── Step 5 — Run the crew ──
    outputs = run_crew(match_context, bartender_mode)

    # ── Step 6 — Print conversation ──
    print_outputs(outputs)

    # ── Step 7 — Update memories ──
    print("💾 Updating memories...")
    update_memories(match_data, outputs, match_id)
    print(f"📊 Total sessions: {get_session_count()}")

    # ── Step 8 — Update website ──
    update_site(match_data, outputs, session_num)

    # ── Step 9 — Bartender status ──
    if bartender_mode == "prediction":
        print("\n🍺 THE BARTENDER HAS SPOKEN.")
    elif bartender_mode == "closing":
        print("\n🍺 THE BARTENDER HAS CLOSED THE TOURNAMENT.")


def run_test_session():
    """
    Dry run with hardcoded match — verifies full pipeline.
    Remove after June 11 when live data is available.
    """
    match_data = {
        "match_id": "test_dry_run_002",
        "date": "2026-06-08",
        "home_team": "Germany",
        "away_team": "Argentina",
        "home_score": 1,
        "away_score": 2,
        "goals": [
            {"minute": 22, "team": "Argentina", "scorer": "Messi"},
            {"minute": 55, "team": "Germany", "scorer": "Havertz"},
            {"minute": 87, "team": "Argentina", "scorer": "Alvarez"}
        ],
        "red_cards": [],
        "stage": "Group Stage",
        "venue": "AT&T Stadium, Dallas",
        "result": "Argentina win",
        "match_context": """
Match: Germany 1 - 2 Argentina
Result: Argentina win
Stage: Group Stage
Venue: AT&T Stadium, Dallas
Date: 2026-06-08
Scorers: Messi 22' (Argentina) | Havertz 55' (Germany) | Alvarez 87' (Argentina)
Red Cards: None
"""
    }

    match_id = match_data["match_id"]
    match_context = match_data["match_context"]

    if already_ran(match_id):
        print("⚠️  Test session already ran.")
        return

    session_num = get_session_count() + 1
    print_session_header(match_data, session_num)

    if should_bartender_close():
        bartender_mode = "closing"
    elif should_bartender_predict():
        bartender_mode = "prediction"
    else:
        bartender_mode = "silent"

    # Run crew
    outputs = run_crew(match_context, bartender_mode)

    # Print
    print_outputs(outputs)

    # Update memories
    print("💾 Updating memories...")
    update_memories(match_data, outputs, match_id)
    print(f"📊 Total sessions: {get_session_count()}")

    # Update website
    update_site(match_data, outputs, session_num)

    print("✅ Test session complete.")


if __name__ == "__main__":
    run_test_session()  # swap to run_session() on June 11