import json
import os

# Base directory — always points to the memory/ folder
MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory")


def load_agent_memory(agent_name):
    file_path = os.path.join(MEMORY_DIR, f"{agent_name.lower()}.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_agent_memory(agent_name, data):
    file_path = os.path.join(MEMORY_DIR, f"{agent_name.lower()}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_all_agents():
    agents = ["cadu", "rodrigo", "gary", "klaus", "antoine"]
    return {agent: load_agent_memory(agent) for agent in agents}


def get_recent_diary(agent_name, entries=5):
    memory = load_agent_memory(agent_name)
    diary = memory.get("tournament_diary", [])
    return diary[-entries:] if len(diary) > entries else diary


def update_mood(agent_name, deltas):
    memory = load_agent_memory(agent_name)
    for mood_key, delta in deltas.items():
        if mood_key in memory["mood_scores"]:
            current = memory["mood_scores"][mood_key]
            memory["mood_scores"][mood_key] = max(0, min(100, current + delta))
    save_agent_memory(agent_name, memory)


def increment_rivalry_count(agent_name, joke_key):
    memory = load_agent_memory(agent_name)
    if joke_key in memory["rivalry"]["running_jokes"]:
        memory["rivalry"]["running_jokes"][joke_key] += 1
    save_agent_memory(agent_name, memory)


def add_diary_entry(agent_name, entry):
    memory = load_agent_memory(agent_name)
    memory["tournament_diary"].append(entry)
    save_agent_memory(agent_name, memory)


def update_team_status(agent_name, status):
    memory = load_agent_memory(agent_name)
    memory["team_status"] = status
    save_agent_memory(agent_name, memory)
