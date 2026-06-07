import json
import os
from utils.memory_manager import load_agent_memory

AGENTS = ["cadu", "rodrigo", "gary", "klaus", "antoine"]


def already_ran(match_id: str) -> bool:
    """
    Check if this match has already been discussed in the bar.
    Checks against Cadu's diary — if it's there, all agents ran.
    Returns True if session already ran, False if it's new.
    """
    try:
        memory = load_agent_memory("cadu")
        diary = memory.get("tournament_diary", [])
        ran_ids = [entry["match_id"] for entry in diary]
        return match_id in ran_ids

    except Exception as e:
        print(f"⚠️  Session guard error: {e}")
        return False


def mark_session_complete(match_id: str, match_data: dict):
    """
    After a session runs successfully — add diary entry to all 5 agents.
    match_data: the clean match dictionary from match_fetcher
    """
    for agent_name in AGENTS:
        try:
            memory = load_agent_memory(agent_name)

            # Determine if this agent's team played tonight
            agent_country_map = {
                "cadu": "Brazil",
                "rodrigo": "Argentina",
                "gary": "England",
                "klaus": "Germany",
                "antoine": "France"
            }

            agent_country = agent_country_map[agent_name]
            my_team_played = (
                agent_country == match_data["home_team"] or
                agent_country == match_data["away_team"]
            )

            # Determine result for this agent's team
            if my_team_played:
                if match_data["result"] == f"{agent_country} win":
                    team_result = "won"
                elif match_data["result"] == "Draw":
                    team_result = "drew"
                else:
                    team_result = "lost"
            else:
                team_result = "not_playing"

            # Build diary entry
            entry = {
                "match_id": match_id,
                "date": match_data["date"],
                "match": f"{match_data['home_team']} {match_data['home_score']}-{match_data['away_score']} {match_data['away_team']}",
                "stage": match_data["stage"],
                "my_team_played": my_team_played,
                "team_result": team_result,
                "reaction_summary": ""  # filled after session runs
            }

            memory["tournament_diary"].append(entry)

            # Save updated memory
            from utils.memory_manager import save_agent_memory
            save_agent_memory(agent_name, memory)

        except Exception as e:
            print(f"⚠️  Could not update diary for {agent_name}: {e}")


def update_reaction_summary(agent_name: str, match_id: str, summary: str):
    """
    After each agent speaks — store a short summary of their reaction.
    This becomes part of their diary context for future sessions.
    summary: first 150 chars of their response
    """
    try:
        memory = load_agent_memory(agent_name)
        diary = memory.get("tournament_diary", [])

        # Find the entry for this match and update summary
        for entry in diary:
            if entry["match_id"] == match_id:
                entry["reaction_summary"] = summary[:150]
                break

        from utils.memory_manager import save_agent_memory
        save_agent_memory(agent_name, memory)

    except Exception as e:
        print(f"⚠️  Could not update reaction summary for {agent_name}: {e}")


def get_session_count() -> int:
    """
    How many sessions have run so far this tournament.
    Used to determine when bartender prediction triggers.
    """
    try:
        memory = load_agent_memory("cadu")
        return len(memory.get("tournament_diary", []))
    except Exception:
        return 0


def should_bartender_predict() -> bool:
    """
    Bartender prediction triggers at session 32 — end of group stage.
    Returns True when it's time for the bartender to speak.
    """
    count = get_session_count()
    return count == 32


def should_bartender_close() -> bool:
    """
    Bartender closing statement triggers at session 104 — after the final.
    Returns True when the tournament is over.
    """
    count = get_session_count()
    return count >= 104
