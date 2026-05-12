"""
Web engine — state-machine driver for the browser version.

The terminal engine in engine.py uses a synchronous loop with input() prompts.
That doesn't work well in a browser, where user input is event-driven.

Instead, this WebGameDriver exposes the game as a state machine:
  - JS calls render() to get the current state as a JSON-serializable dict
  - JS calls submit(action) when the user clicks a button
  - The driver mutates state and returns a fresh render

Shared with the terminal version: Player, Event, Action, Job, Weekend,
Ending modules — all the actual game logic. Only the orchestration layer
differs.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from .action import DAILY_TIME_BLOCKS, DailyPlan, eat, rest, study, use_stimulants, work
from .ending import (
    ENDING_TITLES,
    check_instant_endings,
    evaluate_final_ending,
    get_ending_text,
    get_ending_title,
)
from .event import Event, EventManager, _apply_effects, load_events
from .exam import run_exams
from .job import JOB_REGISTRY, available_jobs
from .player import COURSES, Player, SKILLS
from .weekend import WEEKEND_ACTIVITIES


# Game states ----------------------------------------------------------------
STATE_TITLE = "title"
STATE_NAME_INPUT = "name_input"
STATE_MORNING_PLAN = "morning_plan"        # picking preset / custom
STATE_CUSTOM_PLAN = "custom_plan"          # filling out custom hours
STATE_WEEKEND_PICK = "weekend_pick"
STATE_EVENT_CHOICE = "event_choice"        # event with choices
STATE_DAY_RESULT = "day_result"            # show what happened today
STATE_EXAM = "exam"
STATE_ENDING = "ending"


# Preset plans (re-implemented here so we don't depend on engine.py) --------
def _preset_balanced(player: Player) -> DailyPlan:
    plan = DailyPlan()
    sorted_c = sorted(player.courses.items(), key=lambda kv: kv[1])
    plan.study[sorted_c[0][0]] = 2
    plan.study[sorted_c[1][0]] = 2
    plan.rest = 2
    jobs = available_jobs(player)
    if jobs:
        plan.work[max(jobs, key=lambda j: j.hourly_pay(player)).key] = 2
    return plan


def _preset_grind(player: Player) -> DailyPlan:
    plan = DailyPlan()
    sorted_c = sorted(player.courses.items(), key=lambda kv: kv[1])
    plan.study[sorted_c[0][0]] = 3
    plan.study[sorted_c[1][0]] = 2
    plan.study[sorted_c[2][0]] = 1
    plan.rest = 2
    return plan


def _preset_hustle(player: Player) -> DailyPlan:
    plan = DailyPlan()
    plan.study[COURSES[0]] = 1
    jobs = available_jobs(player)
    if jobs:
        plan.work[max(jobs, key=lambda j: j.hourly_pay(player)).key] = 5
    plan.rest = 2
    return plan


def _preset_recovery(player: Player) -> DailyPlan:
    plan = DailyPlan()
    plan.rest = 6
    plan.study[COURSES[0]] = 2
    return plan


PRESETS = {
    "balanced": ("Balanced",     "2h study weakest x2 + 2h work + 2h rest", _preset_balanced),
    "grind":    ("Study Grind",  "6h study + 2h rest",                      _preset_grind),
    "hustle":   ("Hustle",       "5h work + 1h study + 2h rest",            _preset_hustle),
    "recovery": ("Recovery",     "6h rest + 2h study",                      _preset_recovery),
}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

class WebGameDriver:
    """State-machine driver intended to be called from JavaScript."""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent / "data")
        self.events = load_events(self.data_dir / "events.json")
        self.event_manager = EventManager(self.events)
        self.player: Optional[Player] = None
        self.state: str = STATE_TITLE
        self.pending_event: Optional[Event] = None
        self.last_messages: List[str] = []
        self.ending_id: Optional[str] = None

    # -- public API ----------------------------------------------------
    def render(self) -> Dict[str, Any]:
        """Return the full UI state for JS to render."""
        return {
            "state": self.state,
            "player": self._player_to_dict() if self.player else None,
            "messages": list(self.last_messages),
            "options": self._current_options(),
            "pending_event": self._pending_event_to_dict(),
            "ending": self._ending_to_dict() if self.state == STATE_ENDING else None,
        }

    def submit(self, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply a user action. Returns the post-action state via render().

        action is one of:
          - "start_new"            — begin from title screen
          - "set_name" payload={"name":...}
          - "pick_preset" payload={"preset":"balanced"|"grind"|...}
          - "tweak_preset"          — switch to custom planning starting from current preset
          - "submit_custom" payload={"plan":{...}}
          - "pick_weekend" payload={"key":"rest"|"social"|...}
          - "pick_event_choice" payload={"index":0}
          - "next_day"              — acknowledge day result, advance
          - "run_exams"
          - "restart"
          - "save"                  — write to local storage (handled by JS)
        """
        # Convert JsProxy (when called from JavaScript via PyScript)
        # to a real Python dict. If `payload` is already a Python dict
        # or None, the to_py() call won't exist and we fall through.
        if payload is not None:
            try:
                payload = payload.to_py()
            except (AttributeError, TypeError):
                pass
        payload = payload or {}
        try:
            if action == "start_new":
                self.state = STATE_NAME_INPUT
            elif action == "set_name":
                name = payload.get("name", "Student").strip() or "Student"
                self.player = Player(name=name)
                self.player.log(f"Welcome to USYD, {name}.")
                self.state = STATE_MORNING_PLAN if not self.player.is_weekend else STATE_WEEKEND_PICK
            elif action == "pick_preset":
                self._handle_pick_preset(payload.get("preset", "balanced"))
            elif action == "tweak_preset":
                self.state = STATE_CUSTOM_PLAN
            elif action == "submit_custom":
                self._handle_submit_custom(payload.get("plan", {}))
            elif action == "pick_weekend":
                self._handle_pick_weekend(payload.get("key", "rest"))
            elif action == "pick_event_choice":
                self._handle_event_choice(int(payload.get("index", 0)))
            elif action == "next_day":
                self._handle_next_day()
            elif action == "run_exams":
                self._handle_run_exams()
            elif action == "restart":
                self.player = None
                self.state = STATE_TITLE
                self.last_messages = []
                self.ending_id = None
            elif action == "load_save" and payload.get("data"):
                self.player = Player.from_dict(payload["data"])
                self.state = (
                    STATE_EXAM if self.player.exam_phase
                    else STATE_WEEKEND_PICK if self.player.is_weekend
                    else STATE_MORNING_PLAN
                )
        except Exception as e:  # never let an exception escape into JS
            self.last_messages = [f"[error] {e}"]
        return self.render()

    # -- handlers ------------------------------------------------------
    def _handle_pick_preset(self, preset_key: str) -> None:
        if not self.player:
            return
        preset = PRESETS.get(preset_key)
        if not preset:
            return
        plan = preset[2](self.player)
        self._execute_plan(plan)

    def _handle_submit_custom(self, plan_data: Dict[str, Any]) -> None:
        if not self.player:
            return
        plan = DailyPlan()
        plan.study = {c: int(plan_data.get("study", {}).get(c, 0)) for c in COURSES}
        plan.work = {k: int(v) for k, v in plan_data.get("work", {}).items() if v}
        plan.rest = int(plan_data.get("rest", 0))
        plan.meal_quality = int(plan_data.get("meal_quality", 2))
        plan.use_stimulants = bool(plan_data.get("use_stimulants", False))
        if not plan.is_valid():
            self.last_messages = [f"Invalid plan: {plan.total_hours()}h used, must be 0..{DAILY_TIME_BLOCKS}"]
            return
        self._execute_plan(plan)

    def _handle_pick_weekend(self, key: str) -> None:
        if not self.player:
            return
        for activity in WEEKEND_ACTIVITIES:
            if activity.key == key:
                msg = activity.apply(self.player)
                self.player.log(f"  > {msg}")
                self.last_messages = [msg]
                # Daily background drain still applies on weekends
                self.player.money -= 30
                self._roll_events_then_advance()
                return

    def _handle_event_choice(self, index: int) -> None:
        if not self.player or not self.pending_event:
            return
        event = self.pending_event
        if event.choices and 0 <= index < len(event.choices):
            choice = event.choices[index]
            effects = dict(choice.get("effects", {}))
            if effects.pop("_roll_lottery", 0):
                if random.random() < 0.005:
                    self.player.won_lottery = True
                    self.player.money += 100000
                    self.last_messages = ["YOU WON THE LOTTERY!", *self.last_messages]
                else:
                    self.last_messages = ["Better luck next time.", *self.last_messages]
            _apply_effects(self.player, effects)
            self.player.log(f"  [{event.icon()}] {event.name}: {choice['label']}")
            self.pending_event = None
            self._roll_one_more_event_or_finish()

    def _handle_next_day(self) -> None:
        if not self.player:
            return
        # Check instant game over
        instant = check_instant_endings(self.player)
        if instant:
            self.ending_id = instant
            self.state = STATE_ENDING
            return
        # Advance day
        if self.player.day == 7:
            self.player.week += 1
            self.player.day = 1
        else:
            self.player.day += 1
        # Switch to exam phase
        if self.player.week >= 14 and not self.player.exam_phase:
            self.player.exam_phase = True
            self.state = STATE_EXAM
            return
        # Determine next state based on day-of-week
        self.state = STATE_WEEKEND_PICK if self.player.is_weekend else STATE_MORNING_PLAN
        self.last_messages = []

    def _handle_run_exams(self) -> None:
        if not self.player:
            return
        results = run_exams(self.player)
        self.last_messages = [
            f"{course}: {score:.1f} {'PASS' if score >= 50 else 'FAIL'}"
            for course, score in results.items()
        ]
        self.ending_id = evaluate_final_ending(self.player)
        self.state = STATE_ENDING

    # -- internal helpers ---------------------------------------------
    def _execute_plan(self, plan: DailyPlan) -> None:
        if not self.player:
            return
        plan.execute(self.player)
        self.player.log(f"Day {self.player.total_day}: plan executed ({plan.total_hours()}h used)")
        self.last_messages = [f"Day plan executed: {plan.total_hours()}h"]
        self._roll_events_then_advance()

    def _roll_events_then_advance(self) -> None:
        """After the plan executes, fire events. If a choice event lands, pause."""
        if not self.player:
            return
        # 60% one event, 30% two, 10% none
        roll = random.random()
        count = 1 if roll < 0.6 else 2 if roll < 0.9 else 0
        for _ in range(count):
            event = self.event_manager.pick(self.player)
            if event is None:
                continue
            if event.choices:
                # Pause for player choice
                self.pending_event = event
                self.state = STATE_EVENT_CHOICE
                return
            else:
                event.apply(self.player)
                self.player.log(f"{event.icon()} {event.name}")
                self.last_messages.append(f"{event.icon()} {event.name} — {event.description}")
        # All events resolved without prompting
        self.state = STATE_DAY_RESULT

    def _roll_one_more_event_or_finish(self) -> None:
        """After a choice-event resolves, possibly fire one more, then DAY_RESULT."""
        if not self.player:
            return
        # 30% chance of one more event after a choice event
        if random.random() < 0.3:
            event = self.event_manager.pick(self.player)
            if event:
                if event.choices:
                    self.pending_event = event
                    self.state = STATE_EVENT_CHOICE
                    return
                event.apply(self.player)
                self.player.log(f"{event.icon()} {event.name}")
                self.last_messages.append(f"{event.icon()} {event.name} — {event.description}")
        self.state = STATE_DAY_RESULT

    # -- serialisation ------------------------------------------------
    def _player_to_dict(self) -> Dict[str, Any]:
        p = self.player
        assert p is not None
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return {
            "name": p.name,
            "week": p.week,
            "day": p.day,
            "day_name": weekdays[p.day - 1],
            "total_day": p.total_day,
            "is_weekend": p.is_weekend,
            "exam_phase": p.exam_phase,
            "energy": p.energy,
            "health": p.health,
            "money": p.money,
            "courses": dict(p.courses),
            "skills": dict(p.skills),
            "addiction_uses": p.addiction_uses,
            "ra_days": p.ra_days,
            "prof_favor": p.prof_favor,
            "won_lottery": p.won_lottery,
            "event_log": list(p.event_log),
            "exam_scores": dict(p.exam_scores),
            "average_academic": p.average_academic,
        }

    def _pending_event_to_dict(self) -> Optional[Dict[str, Any]]:
        if not self.pending_event:
            return None
        e = self.pending_event
        return {
            "name": e.name,
            "description": e.description,
            "icon": e.icon(),
            "choices": [{"label": c["label"]} for c in (e.choices or [])],
        }

    def _ending_to_dict(self) -> Optional[Dict[str, Any]]:
        if not self.ending_id:
            return None
        return {
            "id": self.ending_id,
            "title": get_ending_title(self.ending_id),
            "text": get_ending_text(self.ending_id),
        }

    def _current_options(self) -> Dict[str, Any]:
        """Return state-specific UI options (e.g. preset list, jobs, weekend acts)."""
        if not self.player:
            return {}
        if self.state == STATE_MORNING_PLAN:
            return {
                "presets": [
                    {"key": k, "name": v[0], "description": v[1]}
                    for k, v in PRESETS.items()
                ],
            }
        if self.state == STATE_CUSTOM_PLAN:
            return {
                "courses": list(COURSES),
                "jobs": [
                    {"key": j.key, "name": j.name, "pay": j.hourly_pay(self.player), "skill": j.skill}
                    for j in available_jobs(self.player)
                ],
                "max_hours": DAILY_TIME_BLOCKS,
            }
        if self.state == STATE_WEEKEND_PICK:
            return {
                "activities": [
                    {"key": a.key, "label": a.label, "description": a.description}
                    for a in WEEKEND_ACTIVITIES
                ],
            }
        return {}
