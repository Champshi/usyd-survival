"""
Game engine — the main game loop.

This module is the conductor: title screen, save/load menu, daily turn loop,
exam phase switch, ending evaluation, credits.

Demonstrates:
- Controlled exception handling for robust input
- Generator-style random sampling
- Composition (engine builds Player, EventManager, etc.)
"""

from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Dict, List, Optional

from . import save as save_module
from . import ui
from .action import DailyPlan, DAILY_TIME_BLOCKS, use_stimulants
from .ending import (
    check_instant_endings,
    evaluate_final_ending,
    get_ending_text,
    get_ending_title,
)
from .event import Event, EventManager, load_events
from .exam import run_exams
from .job import JOB_REGISTRY, available_jobs
from .player import COURSES, Player
from .weekend import WEEKEND_ACTIVITIES, WEEKEND_REGISTRY


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# Preset daily plans — let the player skip the form for a fast play
# ---------------------------------------------------------------------------

def _preset_balanced(player: Player) -> DailyPlan:
    plan = DailyPlan()
    # Spread 4h of study across the weakest two courses
    sorted_courses = sorted(player.courses.items(), key=lambda kv: kv[1])
    plan.study[sorted_courses[0][0]] = 2
    plan.study[sorted_courses[1][0]] = 2
    plan.rest = 2
    jobs = available_jobs(player)
    if jobs:
        plan.work[max(jobs, key=lambda j: j.hourly_pay(player)).key] = 2
    return plan


def _preset_grind(player: Player) -> DailyPlan:
    plan = DailyPlan()
    sorted_courses = sorted(player.courses.items(), key=lambda kv: kv[1])
    plan.study[sorted_courses[0][0]] = 3
    plan.study[sorted_courses[1][0]] = 2
    plan.study[sorted_courses[2][0]] = 1
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


PRESETS = [
    ("Balanced  (2h study weakest x2 + 2h work + 2h rest)", _preset_balanced),
    ("Study Grind (6h study + 2h rest)",                    _preset_grind),
    ("Hustle    (5h work + 1h study + 2h rest)",            _preset_hustle),
    ("Recovery  (6h rest + 2h study)",                      _preset_recovery),
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class GameEngine:
    """The top-level game controller."""

    def __init__(self) -> None:
        self.player: Optional[Player] = None
        self.event_manager: Optional[EventManager] = None

    # -- entry point ----------------------------------------------------
    def run(self) -> None:
        self._load_event_manager()
        self._title_screen_loop()

    def _load_event_manager(self) -> None:
        events = load_events(DATA_DIR / "events.json")
        self.event_manager = EventManager(events)

    # -- title screen ---------------------------------------------------
    def _title_screen_loop(self) -> None:
        while True:
            ui.show_title()
            options = ["New Game"]
            if save_module.has_save():
                options.append("Continue")
            options.extend(["How to Play", "Quit"])

            ui.console.print()
            for i, opt in enumerate(options, 1):
                ui.console.print(f"  [bold cyan]{i}[/bold cyan]. {opt}")
            ui.console.print()

            choice = ui.prompt("Choose an option", default="1")
            if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
                ui.warn("Invalid choice — try again.")
                time.sleep(0.6)
                continue

            picked = options[int(choice) - 1]
            if picked == "New Game":
                self._start_new_game()
            elif picked == "Continue":
                loaded = save_module.load_game()
                if loaded is None:
                    ui.error("Save file is corrupted or missing.")
                    time.sleep(1.5)
                    continue
                self.player = loaded
                self._main_loop()
            elif picked == "How to Play":
                self._show_help()
            elif picked == "Quit":
                ui.console.print("\n[bold magenta]See you on Eastern Avenue.[/bold magenta]\n")
                return

    def _show_help(self) -> None:
        ui.console.clear()
        ui.console.print(
            "[bold cyan]How to Play[/bold cyan]\n\n"
            "You are a USYD postgrad CS student. You have 13 weeks of classes\n"
            "plus 2 weeks of exams. Each weekday you allocate 8 hours of time\n"
            "across studying (per course), part-time work (per job), rest, and\n"
            "eating. Random life events fire daily — some good, some bad.\n\n"
            "[bold yellow]4 ways to die instantly:[/bold yellow]\n"
            "  - Health hits 0\n"
            "  - Money goes below -$1000\n"
            "  - 20+ uses of stimulants (addiction ending)\n"
            "  - Win the lottery (you stop caring)\n\n"
            "[bold green]4 ways to graduate:[/bold green]\n"
            "  - Honours (avg exam >= 85)\n"
            "  - Work King (max skill >= 90)\n"
            "  - PhD scholarship (30+ RA days, avg >= 80, prof favour)\n"
            "  - Plain pass (all 4 exams >= 50)\n\n"
            "[bold red]1 way to fail:[/bold red]\n"
            "  - Any exam < 50 = withdrawn\n"
        )
        ui.prompt("Press Enter to return")

    # -- new game / character creation ---------------------------------
    def _start_new_game(self) -> None:
        ui.console.clear()
        ui.console.print("[bold magenta]:: NEW GAME ::[/bold magenta]\n")
        name = ui.prompt("What's your character's name?", default="Champ")
        self.player = Player(name=name)
        self.player.log(f"Welcome to USYD, {name}.")
        self._main_loop()

    # -- main daily loop ------------------------------------------------
    def _main_loop(self) -> None:
        assert self.player is not None
        ending: Optional[str] = None

        while ending is None:
            # Switch into exam phase at week 14
            if self.player.week >= 14 and not self.player.exam_phase:
                self.player.exam_phase = True

            # Show dashboard
            ui.show_dashboard(self.player)

            # Exam mode runs once for both weeks
            if self.player.exam_phase:
                ending = self._run_exam_phase()
                break

            # Weekday vs weekend
            if self.player.is_weekend:
                self._run_weekend_day()
            else:
                self._run_weekday()

            # Roll random event(s)
            self._fire_daily_events()

            # Check instant game over
            ending = check_instant_endings(self.player)
            if ending:
                break

            # End of day - advance
            self._advance_day()
            time.sleep(0.4)

        # Finished — show ending
        self._show_ending(ending)

    # -- weekday turn ---------------------------------------------------
    def _run_weekday(self) -> None:
        assert self.player is not None
        ui.console.print()
        ui.console.print(f"[bold yellow]:: Morning planning — Week {self.player.week}, Day {self.player.day} ::[/bold yellow]")
        ui.console.print(f"You have [bold]{DAILY_TIME_BLOCKS}h[/bold] of active time today.\n")

        plan = self._build_plan_via_menu()
        ui.console.print()
        ui.info("Executing today's plan…")
        time.sleep(0.4)
        plan.execute(self.player)
        self.player.log(f"Day {self.player.total_day}: plan executed ({plan.total_hours()}h used)")

    def _build_plan_via_menu(self) -> DailyPlan:
        """Show preset menu first; option to customise from there."""
        assert self.player is not None
        ui.console.print("[bold cyan]Pick a preset, or customise:[/bold cyan]")
        for i, (label, _fn) in enumerate(PRESETS, 1):
            ui.console.print(f"  [cyan]{i}[/cyan]. {label}")
        ui.console.print(f"  [cyan]{len(PRESETS)+1}[/cyan]. Custom (manual hour-by-hour)")
        ui.console.print()

        while True:
            choice = ui.prompt("Choose", default="1")
            if choice.isdigit() and 1 <= int(choice) <= len(PRESETS):
                base_plan = PRESETS[int(choice) - 1][1](self.player)
                # Optionally let them tweak after preset
                tweak = ui.prompt("Tweak this plan? (y/N)", default="n").lower()
                if tweak.startswith("y"):
                    return self._customise_plan(base_plan)
                return base_plan
            if choice.isdigit() and int(choice) == len(PRESETS) + 1:
                return self._customise_plan(DailyPlan())
            ui.warn("Invalid choice.")

    def _customise_plan(self, plan: DailyPlan) -> DailyPlan:
        """Walk the player through filling out a custom DailyPlan."""
        assert self.player is not None

        def ask_int(prompt_text: str, default_value: int, max_value: int) -> int:
            while True:
                raw = ui.prompt(prompt_text, default=str(default_value))
                try:
                    val = int(raw)
                except ValueError:
                    ui.warn("Please enter a whole number.")
                    continue
                if 0 <= val <= max_value:
                    return val
                ui.warn(f"Must be between 0 and {max_value}.")

        budget = DAILY_TIME_BLOCKS

        ui.console.print("\n[dim]Enter hours for each — we'll show your remaining budget.[/dim]")
        for course in COURSES:
            current = plan.study.get(course, 0)
            hours = ask_int(f"  Study {course} (remaining {budget}h)", current, budget)
            plan.study[course] = hours
            budget -= hours

        ui.console.print("\n[dim]Available jobs:[/dim]")
        jobs = available_jobs(self.player)
        for j in jobs:
            ui.console.print(f"  - {j.key}: {j.name} (${j.hourly_pay(self.player):.0f}/h)")
        for j in jobs:
            current = plan.work.get(j.key, 0)
            hours = ask_int(f"  Work as {j.name} (remaining {budget}h)", current, budget)
            plan.work[j.key] = hours
            budget -= hours

        rest_hours = ask_int(f"  Rest hours (remaining {budget}h)", plan.rest, budget)
        plan.rest = rest_hours

        meal_q = ask_int("  Meal quality (0=skip, 1=noodle, 2=Wentworth, 3=Newtown)", plan.meal_quality, 3)
        plan.meal_quality = meal_q

        if self.player.energy < 30:
            stim = ui.prompt("  Use stimulants? (y/N)", default="n").lower()
            plan.use_stimulants = stim.startswith("y")

        return plan

    # -- weekend turn ---------------------------------------------------
    def _run_weekend_day(self) -> None:
        assert self.player is not None
        ui.console.print()
        ui.console.print(f"[bold magenta]:: Weekend — pick one activity ::[/bold magenta]\n")
        for i, act in enumerate(WEEKEND_ACTIVITIES, 1):
            ui.console.print(f"  [cyan]{i}[/cyan]. {act.label} — [dim]{act.description}[/dim]")
        ui.console.print()

        while True:
            raw = ui.prompt("Choose", default="1")
            if raw.isdigit() and 1 <= int(raw) <= len(WEEKEND_ACTIVITIES):
                activity = WEEKEND_ACTIVITIES[int(raw) - 1]
                msg = activity.apply(self.player)
                self.player.log(f"  > {msg}")
                ui.info(msg)
                time.sleep(0.6)
                # Daily background drains still apply on weekends
                self.player.money -= 30
                return
            ui.warn("Invalid choice.")

    # -- random events -------------------------------------------------
    def _fire_daily_events(self) -> None:
        """Fire 1-2 random events. Events with player choices prompt the user."""
        assert self.player and self.event_manager
        # 60% chance of 1 event, 30% of 2, 10% of none
        roll = random.random()
        count = 1 if roll < 0.6 else 2 if roll < 0.9 else 0
        for _ in range(count):
            event = self.event_manager.pick(self.player)
            if event is None:
                continue
            self._handle_event(event)

    def _handle_event(self, event: Event) -> None:
        """Apply an event, including handling any player choices."""
        assert self.player is not None
        ui.console.print()
        ui.console.print(f"[bold yellow]:: EVENT :: {event.name}[/bold yellow]")
        ui.console.print(f"  {event.description}")

        if event.choices:
            for i, ch in enumerate(event.choices, 1):
                ui.console.print(f"    [cyan]{i}[/cyan]. {ch['label']}")
            while True:
                raw = ui.prompt("Your choice", default="1")
                if raw.isdigit() and 1 <= int(raw) <= len(event.choices):
                    choice = event.choices[int(raw) - 1]
                    effects = dict(choice.get("effects", {}))
                    # Special: lottery roll
                    if effects.pop("_roll_lottery", 0):
                        if random.random() < 0.005:
                            self.player.won_lottery = True
                            self.player.money += 100000
                            ui.big_announce("YOU WON THE LOTTERY!", color="bright_yellow")
                        else:
                            ui.info("Better luck next time.")
                    from .event import _apply_effects  # noqa: WPS437 — internal helper
                    _apply_effects(self.player, effects)
                    self.player.log(f"  [{event.icon()}] {event.name}: {choice['label']}")
                    time.sleep(0.5)
                    return
                ui.warn("Invalid choice.")
        else:
            event.apply(self.player)
            self.player.log(f"{event.icon()} {event.name}")
            time.sleep(0.7)

    # -- day advance ---------------------------------------------------
    def _advance_day(self) -> None:
        assert self.player is not None
        # End-of-week save
        if self.player.day == 7:
            save_module.save_game(self.player)
            self.player.log(f"[Auto-saved end of Week {self.player.week}]")
            self.player.week += 1
            self.player.day = 1
        else:
            self.player.day += 1

    # -- exam phase ----------------------------------------------------
    def _run_exam_phase(self) -> str:
        """Run all 4 exams, evaluate final ending."""
        assert self.player is not None
        ui.console.clear()
        ui.big_announce("EXAM WEEK — Good luck.", color="bright_red")
        time.sleep(1.0)
        results = run_exams(self.player)

        # Show results
        ui.console.print("\n[bold yellow]Exam Results[/bold yellow]")
        for course, score in results.items():
            color = "bright_green" if score >= 85 else "green" if score >= 65 else "yellow" if score >= 50 else "bright_red"
            status = "[bold red]FAIL[/]" if score < 50 else "[bold green]PASS[/]"
            ui.console.print(f"  {course}: [{color}]{score:5.1f}[/]  {status}")
        ui.console.print()

        ui.prompt("Press Enter to see your ending")
        return evaluate_final_ending(self.player)

    # -- ending screen -------------------------------------------------
    def _show_ending(self, ending_id: str) -> None:
        assert self.player is not None
        ui.console.clear()
        title = get_ending_title(ending_id)
        text = get_ending_text(ending_id)
        ui.big_announce(title, color="magenta")
        ui.console.print()
        ui.console.print(text, style="italic")
        ui.console.print()

        # Final stats summary
        ui.console.print("[bold cyan]Final stats:[/bold cyan]")
        ui.console.print(f"  Money:   ${self.player.money:.0f}")
        ui.console.print(f"  Health:  {self.player.health:.0f}/100")
        ui.console.print(f"  Energy:  {self.player.energy:.0f}/100")
        ui.console.print(f"  Best skill: {self.player.best_skill} ({self.player.best_skill_value:.0f})")
        if self.player.exam_scores and any(self.player.exam_scores.values()):
            avg = sum(self.player.exam_scores.values()) / len(self.player.exam_scores)
            ui.console.print(f"  Exam avg: {avg:.1f}")
        ui.console.print()

        save_module.delete_save()
        ui.prompt("Press Enter to return to title")
