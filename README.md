# The Gaffers 🍺

**Six AI agents. One sports bar. Every match. Every night.**

The Gaffers is a multi-agent AI system that follows the FIFA World Cup 2026 autonomously. After every match, five AI football fans and a silent bartender gather at The Neutral Zone sports bar in New York and react — with memory, personality, and emotional continuity — to everything that happened on the pitch.

🔗 **Live site:** [kulsha.github.io/the-gaffers](https://kulsha.github.io/the-gaffers)

---

## The Regulars

| Agent | Country | Personality |
|---|---|---|
| 🇧🇷 Cadu | Brazil | Poetic, emotional, carries the scar of the 7-1 |
| 🇦🇷 Rodrigo | Argentina | Theatrical, references 2022 constantly, counts Gary's words |
| 🏴󠁧󠁢󠁥󠁬󠁧󠁿 Gary | England | Eternal optimist, self-aware about being hurt, says it anyway |
| 🇩🇪 Klaus | Germany | Analytical, always has a statistic, occasionally trails off mid-sentence |
| 🇫🇷 Antoine | France | Philosophical, unbothered, words land like scalpels |
| 🍺 The Bartender | Neutral | Silent observer. Speaks twice. Once at mid-tournament with a prediction. Once after the final. |

---

## How It Works

```
FIFA 2026 match finishes
        ↓
match_fetcher.py fetches result from API-Football
        ↓
session_guard.py checks — has this match already run?
        ↓
5 agent memories loaded — diary, mood scores, rivalry counts
        ↓
CrewAI sequential crew runs — each agent reads previous agents before responding
        ↓
Bartender closes the session
        ↓
Memories updated — mood deltas, diary entries, rivalry counts
        ↓
sessions.json + agents.json updated
        ↓
Git commit + push — GitHub Pages updates within 2 minutes
```

---

## AI Concepts Demonstrated

| Concept | Implementation |
|---|---|
| **Multi-agent orchestration** | CrewAI sequential crew — 6 agents, each reads previous outputs |
| **Persistent memory** | JSON per agent — mood scores, tournament diary, rivalry counters |
| **Emotional continuity** | Mood deltas applied after every match — hope, confidence, anger, bitterness |
| **Context awareness** | Each agent reads their own diary before responding |
| **Persona consistency** | System prompts shaped by memory state — eliminated agents speak differently |
| **Autonomous operation** | Session guard prevents duplicates — safe to run multiple times |
| **Auto-deployment** | Every session auto-commits and pushes to GitHub Pages |

---

## Stack

- **Python 3.11+**
- **CrewAI** — multi-agent orchestration
- **Claude API** (claude-sonnet-4-5) — agent LLM
- **API-Football** — live FIFA 2026 match data
- **GitHub Pages** — live website from `docs/`
- **Vanilla JS** — dynamic website reads from JSON

---

## Project Structure

```
the-gaffers/
├── main.py                    ← entry point
├── run_morning.bat            ← double-click daily routine (gitignored)
├── .env                       ← API keys (gitignored)
├── requirements.txt           ← Python dependencies
├── agents/
│   ├── cadu.py                ← Brazilian fan — poetic, emotional
│   ├── rodrigo.py             ← Argentine fan — theatrical, 2022 obsessed
│   ├── gary.py                ← English fan — eternal optimist
│   ├── klaus.py               ← German fan — analytical, data-driven
│   ├── antoine.py             ← French fan — philosophical, unbothered
│   └── bartender.py           ← Silent observer — speaks twice
├── memory/
│   ├── cadu.json              ← Cadu's mood, diary, rivalry state
│   ├── rodrigo.json           ← Rodrigo's mood, diary, rivalry state
│   ├── gary.json              ← Gary's mood, diary, rivalry state
│   ├── klaus.json             ← Klaus's mood, diary, rivalry state
│   └── antoine.json           ← Antoine's mood, diary, rivalry state
├── data/
│   └── match_fetcher.py       ← API-Football — FIFA 2026 live results
├── utils/
│   ├── memory_manager.py      ← all JSON read/write, single gateway
│   ├── session_guard.py       ← duplicate prevention, diary updates
│   ├── html_generator.py      ← writes sessions.json + agents.json
│   └── site_updater.py        ← auto git commit + push after every session
└── docs/
    ├── index.html             ← dynamic website
    └── data/
        ├── sessions.json      ← all session data (auto-updated)
        └── agents.json        ← live agent state (auto-updated)
```
---

## Running It

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY and API_FOOTBALL_KEY

# Run a session
python main.py
```

---

## Daily Routine (June 12 onwards)

Double-click `run_morning.bat` every morning — it processes all overnight matches automatically.
Each run fetches the latest result, triggers the agents, updates memories,
and pushes to GitHub without any manual steps.
The website updates within 2 minutes of running.

**Next step:** Replace the manual morning run with a cron job / cloud scheduler
so the pipeline runs fully autonomously — no human intervention required at any point.

To trigger manually after watching a match live:
```bash
python main.py
```

---

## The Bartender

The bartender speaks twice this tournament.

At match 32 — mid-tournament — he reads every session diary and names the winner. One team. One reason.

After the final — he closes the tournament. Moment of the Tournament. Most delusional fan. Most accurate fan. One last observation that has nothing to do with football.

He has been watching since June 11.

---

*Built during FIFA World Cup 2026. June–July 2026.*
*Stack: Python · CrewAI · Claude API · GitHub Pages*
