import os
from dotenv import load_dotenv
from crewai import Crew, Task, Process

from agents.cadu import create_cadu
from agents.rodrigo import create_rodrigo
from agents.gary import create_gary
from agents.klaus import create_klaus
from agents.antoine import create_antoine
from agents.bartender import create_bartender

load_dotenv()

# ── HARDCODED MATCH — will be replaced by live API on Jun 8 ──
MATCH_CONTEXT = """
Match: Brazil 2 - 1 France
Scorers: Vinicius Jr 34', Rodrygo 88' (Brazil) | Mbappé 61' (France)
Stage: Group Stage — Group A
Venue: MetLife Stadium, New Jersey
Red Cards: None
"""

def run_session():
    print("\n" + "="*55)
    print("  THE NEUTRAL ZONE · New York")
    print("  FIFA World Cup 2026")
    print(f"  Match: Brazil 2-1 France")
    print("="*55 + "\n")

    # ── Create all agents ──
    cadu    = create_cadu(MATCH_CONTEXT)
    rodrigo = create_rodrigo(MATCH_CONTEXT)
    gary    = create_gary(MATCH_CONTEXT)
    klaus   = create_klaus(MATCH_CONTEXT)
    antoine = create_antoine(MATCH_CONTEXT)
    bartender = create_bartender(mode="silent")

    # ── Create tasks ──
    # Each agent reads the previous agent's output before responding
    # This creates the organic bar conversation feel

    task_cadu = Task(
        description=f"""
        The match just finished: {MATCH_CONTEXT}
        You are sitting in The Neutral Zone sports bar in New York.
        React to this result. Be Cadu. 2-4 sentences maximum.
        """,
        expected_output="A raw, emotional reaction to the match result in Cadu's voice",
        agent=cadu
    )

    task_rodrigo = Task(
        description=f"""
        The match just finished: {MATCH_CONTEXT}
        Cadu just reacted. You heard what he said.
        Now it is your turn. React to the match AND respond to 
        something Cadu said if it deserves a response.
        Be Rodrigo. 2-4 sentences maximum.
        """,
        expected_output="Rodrigo's reaction — to the match and possibly to Cadu",
        agent=rodrigo,
        context=[task_cadu]
    )

    task_gary = Task(
        description=f"""
        The match just finished: {MATCH_CONTEXT}
        Cadu and Rodrigo have both spoken. You heard everything.
        React to the match. Respond to anyone if something they said 
        deserves a response. Be Gary. 2-4 sentences maximum.
        """,
        expected_output="Gary's reaction — to the match and the conversation so far",
        agent=gary,
        context=[task_cadu, task_rodrigo]
    )

    task_klaus = Task(
        description=f"""
        The match just finished: {MATCH_CONTEXT}
        Cadu, Rodrigo and Gary have all reacted. You heard everything.
        React to the match with analysis. Respond to anyone if their 
        reasoning deserves correction. Be Klaus. 2-4 sentences maximum.
        """,
        expected_output="Klaus's analytical reaction — data, tactics, occasional humanity",
        agent=klaus,
        context=[task_cadu, task_rodrigo, task_gary]
    )

    task_antoine = Task(
        description=f"""
        The match just finished: {MATCH_CONTEXT}
        Everyone has spoken. You have heard it all.
        React to the match. Respond to whoever said something 
        worth responding to. Be Antoine. 2-4 sentences maximum.
        """,
        expected_output="Antoine's philosophical reaction — calm, precise, cuts deep",
        agent=antoine,
        context=[task_cadu, task_rodrigo, task_gary, task_klaus]
    )

    task_bartender = Task(
        description=f"""
        You have watched the whole session tonight.
        Five fans reacted to: {MATCH_CONTEXT}
        End the session with one quiet observation.
        One or two sentences maximum. Make it land.
        """,
        expected_output="The bartender's single closing observation for tonight",
        agent=bartender,
        context=[task_cadu, task_rodrigo, task_gary, task_klaus, task_antoine]
    )

    # ── Assemble the crew ──
    crew = Crew(
        agents=[cadu, rodrigo, gary, klaus, antoine, bartender],
        tasks=[
            task_cadu,
            task_rodrigo,
            task_gary,
            task_klaus,
            task_antoine,
            task_bartender
        ],
        process=Process.sequential,
        verbose=False
    )

    # ── Run the session ──
    result = crew.kickoff()

    # ── Print the bar conversation ──
    print("\n🇧🇷 CADU")
    print(task_cadu.output.raw if task_cadu.output else "...")
    print("\n🇦🇷 RODRIGO")
    print(task_rodrigo.output.raw if task_rodrigo.output else "...")
    print("\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 GARY")
    print(task_gary.output.raw if task_gary.output else "...")
    print("\n🇩🇪 KLAUS")
    print(task_klaus.output.raw if task_klaus.output else "...")
    print("\n🇫🇷 ANTOINE")
    print(task_antoine.output.raw if task_antoine.output else "...")
    print("\n🍺 THE BARTENDER")
    print(task_bartender.output.raw if task_bartender.output else "...")

    print("\n" + "="*55 + "\n")


if __name__ == "__main__":
    run_session()