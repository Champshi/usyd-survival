"""
Action system — the player's daily time allocation + action effects.

Each weekday, the player has 8 "time blocks" to spend across:
- Study (per course)
- Work (per job)
- Rest
- Eat (paid action)
- Stimulants (risky action)

Demonstrates:
- Decorators (the @log_action decorator wraps every action with logging)
- Higher-order functions
- functools.wraps for clean decorator behaviour
"""

from __future__ import annotations

import functools
import random
from typing import Callable, Dict

from .job import JOB_REGISTRY, available_jobs
from .player import COURSES, Player

# Each weekday the player has this many "blocks" of time to allocate
DAILY_TIME_BLOCKS = 8


def log_action(action_name: str) -> Callable:
    """
    Decorator that logs every action the player takes.

    Demonstrates the decorator pattern — one of COMP9001's advanced topics.
    Without this decorator, every action function would need its own logging
    boilerplate. Now they all share it.
    """
    def decorator(func: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(func)
        def wrapper(player: Player, *args, **kwargs) -> str:
            message = func(player, *args, **kwargs)
            player.log(f"  > {message}")
            return message
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Atomic actions — each takes (player, hours) and returns a result string
# ---------------------------------------------------------------------------

@log_action("study")
def study(player: Player, hours: int, course: str) -> str:
    """Study a specific course. Diminishing returns at low energy."""
    if hours <= 0:
        return ""
    # Energy multiplier — tired students learn less
    efficiency = 0.4 + 0.6 * (player.energy / 100)
    progress = hours * 1.6 * efficiency
    energy_cost = hours * 6
    player.add_course_progress(course, progress)
    player.energy -= energy_cost
    return f"Studied {course} for {hours}h: +{progress:.1f}% (eff {efficiency:.0%})"


@log_action("work")
def work(player: Player, hours: int, job_key: str) -> str:
    """Work at a specific job."""
    if hours <= 0 or job_key not in JOB_REGISTRY:
        return ""
    job = JOB_REGISTRY[job_key]
    return job.work(player, hours)


@log_action("rest")
def rest(player: Player, hours: int) -> str:
    """Rest restores energy and a little health."""
    if hours <= 0:
        return ""
    energy_gain = hours * 12
    health_gain = hours * 2
    player.energy += energy_gain
    player.health += health_gain
    return f"Rested {hours}h: +{energy_gain} energy, +{health_gain} health"


@log_action("eat")
def eat(player: Player, quality: int) -> str:
    """
    Eat a meal. Quality 1-3:
      1 = instant noodles ($5, +5 energy, +1 health)
      2 = Wentworth food court ($15, +12 energy, +5 health)
      3 = Newtown sit-down ($30, +20 energy, +10 health)
    """
    menu = {
        1: ("Instant noodles", 5, 5, 1),
        2: ("Wentworth food court", 15, 12, 5),
        3: ("Newtown dinner", 30, 20, 10),
    }
    if quality not in menu:
        return ""
    name, cost, e_gain, h_gain = menu[quality]
    if player.money < cost:
        return f"Couldn't afford {name}!"
    player.money -= cost
    player.energy += e_gain
    player.health += h_gain
    return f"Ate {name}: -${cost}, +{e_gain} energy, +{h_gain} health"


@log_action("stimulants")
def use_stimulants(player: Player) -> str:
    """
    Take 'brain booster' pills — illegal stimulants.
    Big energy boost, but health damage and addiction climbs toward bad ending.
    """
    if player.money < 25:
        return "Not enough money for stimulants"
    player.money -= 25
    player.energy += 35
    player.health -= 8
    player.addiction_uses += 1
    return f"Used stimulants: +35 energy, -8 health (addiction: {player.addiction_uses})"


# ---------------------------------------------------------------------------
# Daily plan — the player's morning allocation
# ---------------------------------------------------------------------------

class DailyPlan:
    """
    A morning plan for how to spend today's time blocks.

    Field meanings:
      study: dict mapping course -> hours
      work: dict mapping job_key -> hours
      rest: int hours
      meal_quality: 0=skip, 1/2/3 = quality tier
      use_stimulants: bool
    """

    def __init__(self) -> None:
        self.study: Dict[str, int] = {c: 0 for c in COURSES}
        self.work: Dict[str, int] = {}
        self.rest: int = 0
        self.meal_quality: int = 2
        self.use_stimulants: bool = False

    def total_hours(self) -> int:
        return sum(self.study.values()) + sum(self.work.values()) + self.rest

    def is_valid(self) -> bool:
        return 0 <= self.total_hours() <= DAILY_TIME_BLOCKS

    def execute(self, player: Player) -> None:
        """Apply the entire plan to the player, in order."""
        # Optional stimulants happen first (big energy boost lets you do more)
        if self.use_stimulants:
            use_stimulants(player)

        # Study sessions
        for course, hours in self.study.items():
            if hours > 0:
                study(player, hours, course)

        # Work sessions
        for job_key, hours in self.work.items():
            if hours > 0:
                work(player, hours, job_key)

        # Rest
        if self.rest > 0:
            rest(player, self.rest)

        # Eat at end of day (if affordable)
        if self.meal_quality > 0:
            eat(player, self.meal_quality)

        # Daily background drains: rent ($35) + transport ($8) + utilities ($7)
        player.money -= 50
        # Health-energy coupling: low energy slowly damages health
        if player.energy < 20:
            player.health -= 4
            player.log("  > [!] Exhausted — health is suffering")
        # Skipping meals also hurts
        if self.meal_quality == 0:
            player.health -= 3
            player.energy -= 5
