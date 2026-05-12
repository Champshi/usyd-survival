# USYD Survival Simulator

A text-based life simulation game built in Python. You play a USYD postgraduate
CS student trying to balance academics, finances, and health across one full
semester (13 study weeks + 2 exam weeks). Nine different endings reward — or
punish — your choices.

Built for **COMP9001 — Python Programming** Final Project.

---

## How to Run

The game has **two ways to play**:

### Option 1 — Web version (no install required)

Open `index.html` via a local web server. No Python installation needed; the
game runs entirely in your browser via PyScript.

```bash
cd usyd_survival
python -m http.server 8000
# Then open http://localhost:8000 in Chrome / Firefox / Safari
```

To make it publicly playable (great for the Padlet post), see `WEB_DEPLOYMENT.md`
for free GitHub Pages hosting.

### Option 2 — Terminal version

You will need Python 3.9 or newer.

```bash
# 1) (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate         # macOS / Linux
venv\Scripts\activate            # Windows

# 2) install the only dependency
pip install -r requirements.txt

# 3) play
python main.py
```

The only library used is **Rich** (for the coloured terminal UI).

---

## How to Play

Each weekday morning you allocate **8 hours** of "active time" across:

- **Study** — pick which of your four courses to invest in
- **Work** — earn money + level up a skill (pay scales with skill level)
- **Rest** — recover energy and a little health
- **Eat** — buy a meal (3 quality tiers, cost vs. benefit trade-off)
- **Stimulants** — risky! Big energy boost but addiction climbs toward a bad ending

Pick from one of four **preset plans** for fast play, or go fully **custom**
hour-by-hour.

On weekends, you choose **one** activity: rest day, social outing, weekend
shift, gym session, or a "study grind" lock-in.

Throughout the day, **1–2 random events** fire — found cash, train delays,
group project drama, lottery offers, RA invitations, and more.

Your **save file** is written automatically at the end of every week.

---

## Endings

There are **9 endings** to discover:

| # | Ending | How to get it |
|---|---|---|
| 1 | **Top of the Class (Honours)** | Final exam average ≥ 85, all passed, healthy |
| 2 | **King of the Side Hustle** | Max one skill at 90+ while passing all exams |
| 3 | **You Did It (Pass)** | All four exams ≥ 50 |
| 4 | **Bankrupt on King St** | Money drops below -$1000 |
| 5 | **Withdrawn (Dropout)** | Any exam < 50 |
| 6 | **Lights Out** | Health hits 0 |
| 7 | **A Winning Ticket** *(hidden)* | Win the lottery from a rare random event |
| 8 | **Full Scholarship PhD** *(hidden)* | 30+ days as Research Assistant + average ≥ 80 + professor's favour |
| 9 | **Lost in the Haze** | 20+ uses of stimulants (addiction ending) |

---

## Project Structure

```
usyd_survival/
├── main.py                   # Terminal entry point
├── requirements.txt
├── README.md
├── WEB_DEPLOYMENT.md         # GitHub Pages deployment guide
├── PADLET_AND_PRESENTATION.md
│
├── index.html                # Web version entry (PyScript)
├── style.css                 # Pixel-style web CSS
├── app.js                    # JS bridge to the Python game
├── pyscript.toml             # PyScript file manifest
│
├── game/
│   ├── __init__.py
│   ├── player.py             # Player class — all game state
│   ├── event.py              # Event base + subclasses + JSON loader
│   ├── action.py             # Daily plan + study/work/rest/eat/stimulants
│   ├── job.py                # Part-time job system + skills
│   ├── weekend.py            # Weekend single-choice activities
│   ├── exam.py               # Final exam scoring
│   ├── ending.py             # 9 endings + flavour text
│   ├── save.py               # JSON save/load (terminal)
│   ├── ui.py                 # Rich terminal UI
│   ├── engine.py             # Terminal main game loop
│   └── web_engine.py         # State-machine driver for browser
├── data/
│   └── events.json           # 30 USYD-flavoured random events
└── saves/
    └── savegame.json         # Auto-created (terminal save)
```

---

## Advanced Python Concepts Used

The COMP9001 brief requires at least 2 advanced concepts. This project uses **9+**:

1. **Object-Oriented Programming** — `Player`, `Event`, `Job`, `WeekendActivity` are full classes
2. **Class inheritance / polymorphism** — `Event` → `GoodEvent` / `BadEvent` / `NeutralEvent` / `HiddenEvent`, each overrides `icon()`
3. **Decorators** — `@log_action` decorator wraps every action with logging (see `action.py`)
4. **File I/O & JSON** — events loaded from `data/events.json`, save/load via JSON in `save.py`
5. **Exception handling** — `try/except` for corrupted saves, malformed JSON, invalid input
6. **List & dict comprehensions** — used for filtering eligible events, building stat tables, etc.
7. **Lambda expressions** — for sorting jobs by pay, filtering activities, in `weekend.py`
8. **Property setters** — clamped stats (`energy`, `health` properties on `Player`)
9. **Type hints** — used throughout for clarity
10. **Module organisation** — split into 10+ focused files, importable as a package
11. **External library use** — `rich` for terminal UI, `random` for events, `json` for saves

---

## Tips for Survival

- **Money is sneaky.** $50/day in background costs (rent, transport, utilities) means you NEED to work some weekdays.
- **Tutoring (week 3+)** pays better than the cafe job. Switch when it unlocks.
- **Sleep matters.** Energy below 20 damages your health every day.
- **Final exams scale with energy & health**, not just course progress. Cramming while exhausted scores worse than fewer hours while rested.
- **The hidden PhD ending** requires committing to RA work early — week 4 onwards. It's not for everyone.
- **The lottery** has a 0.5% chance per ticket. Don't quit your day job.

---

## Author

Champ — University of Sydney, 2026 Semester 1.
