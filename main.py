import os
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
    get_processed_match_ids,
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
    cadu      = create_cadu(match_context)
    rodrigo   = create_rodrigo(match_context)
    gary      = create_gary(match_context)
    klaus     = create_klaus(match_context)
    antoine   = create_antoine(match_context)
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
        Cadu has already reacted. You heard him.
        You MUST give a DIFFERENT take — do NOT repeat or echo what Cadu said.
        Bring your own angle. Disagree if you can. Be Rodrigo. 2-4 sentences maximum.
        """,
        expected_output="Rodrigo's unique reaction — different from Cadu's",
        agent=rodrigo,
        context=[task_cadu]
    )
    task_gary = Task(
        description=f"""
        The match just finished: {match_context}
        Cadu and Rodrigo have both spoken. You heard everything.
        Do NOT repeat what either of them said. Bring something new.
        React in Gary's voice. 2-4 sentences maximum.
        """,
        expected_output="Gary's unique reaction — different from Cadu and Rodrigo",
        agent=gary,
        context=[task_cadu, task_rodrigo]
    )
    task_klaus = Task(
        description=f"""
        The match just finished: {match_context}
        Cadu, Rodrigo and Gary have all reacted. You heard everything.
        Do NOT repeat what anyone said. Add data, statistics, analysis they missed.
        Correct someone if their reasoning is wrong. Be Klaus. 2-4 sentences maximum.
        """,
        expected_output="Klaus's analytical reaction with at least one statistic — unique perspective",
        agent=klaus,
        context=[task_cadu, task_rodrigo, task_gary]
    )
    task_antoine = Task(
        description=f"""
        The match just finished: {match_context}
        Everyone has spoken. You have heard it all.
        Do NOT repeat what anyone said. Say something none of them thought to say.
        Be philosophical. Be Antoine. 2-4 sentences maximum.
        """,
        expected_output="Antoine's philosophical reaction — a perspective nobody else raised",
        agent=antoine,
        context=[task_cadu, task_rodrigo, task_gary, task_klaus]
    )
    task_bartender = Task(
        description=f"""
        You have watched the whole session tonight.
        Five fans reacted to: {match_context}
        End the session in your mode: {bartender_mode}
        Say something that cuts through all the noise. One observation nobody made.
        """,
        expected_output="The bartender's closing — one sharp observation",
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
    Main session runner — uses live FIFA 2026 data.
    Runs autonomously from June 11 onwards.
    """

    # ── Step 1 — Fetch latest unprocessed match ──
    print("\n⚽ Fetching latest FIFA 2026 match...")
    processed_ids = get_processed_match_ids()
    match_data = fetch_latest_match(exclude_ids=processed_ids)

    if not match_data:
        print("⚠️  No FIFA 2026 match available.")
        print("Come back after the next match finishes.")
        sys.exit(0)

    match_id = match_data["match_id"]
    match_context = match_data["match_context"]

    # ── Step 2 — Session guard (safety net) ──
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
    update_site(match_data, outputs, session_num, bartender_mode)

    # ── Step 9 — Bartender status ──
    if bartender_mode == "prediction":
        print("\n🍺 THE BARTENDER HAS SPOKEN.")
    elif bartender_mode == "closing":
        print("\n🍺 THE BARTENDER HAS CLOSED THE TOURNAMENT.")


def run_test_session():
    """
    Dry run with hardcoded match — verifies full pipeline.
    """
    match_data = {
        "match_id": "test_dry_run_007",
        "date": "2026-06-09",
        "home_team": "Brazil",
        "away_team": "Argentina",
        "home_score": 1,
        "away_score": 0,
        "goals": [{"minute": 55, "team": "Brazil", "scorer": "Vinicius Jr"}],
        "red_cards": [],
        "stage": "Quarter Final",
        "venue": "MetLife Stadium, New Jersey",
        "result": "Brazil win",
        "match_context": """
Match: Brazil 1 - 0 Argentina
Result: Brazil win
Stage: Quarter Final
Venue: MetLife Stadium, New Jersey
Date: 2026-06-09
Scorers: Vinicius Jr 55' (Brazil)
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

    outputs = run_crew(match_context, bartender_mode)
    print_outputs(outputs)

    print("💾 Updating memories...")
    update_memories(match_data, outputs, match_id)
    print(f"📊 Total sessions: {get_session_count()}")

    update_site(match_data, outputs, session_num, bartender_mode)
    print("✅ Test session complete.")


if __name__ == "__main__":
    run_session()