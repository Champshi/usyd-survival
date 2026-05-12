"""
Weekend activity system — on Saturday/Sunday, the player picks ONE activity.

Different from weekdays, where you allocate time across many actions —
weekends are about a single defining choice each day.

Demonstrates:
- A registry of named activities (dict of named functions)
- Lambda expressions for compact effect definitions
"""

from __future__ import annotations

from typing import Callable, Dict, List

from .player import Player


class WeekendActivity:
    """One weekend choice. apply() mutates the player and returns a description."""

    def __init__(
        self,
        key: str,
        label: str,
        description: str,
        apply_fn: Callable[[Player], str],
    ) -> None:
        self.key = key
        self.label = label
        self.description = description
        self.apply_fn = apply_fn

    def apply(self, player: Player) -> str:
        return self.apply_fn(player)


# Lambda-based effect functions keep activity definitions compact
def _rest_day(p: Player) -> str:
    p.energy += 25
    p.health += 8
    return "Slept in, ate well, watched a movie. +25 energy, +8 health"


def _social_outing(p: Player) -> str:
    if p.money < 50:
        p.energy -= 5
        return "Couldn't afford the outing — felt left out. -5 energy"
    p.money -= 50
    p.energy += 15
    p.health += 6
    return "Brunch in Newtown with friends. -$50, +15 energy, +6 health"


def _weekend_shift(p: Player) -> str:
    # Take whichever job has the highest current pay
    from .job import available_jobs  # local import to avoid cycle
    jobs = available_jobs(p)
    if not jobs:
        return "No weekend shift available."
    job = max(jobs, key=lambda j: j.hourly_pay(p))
    earned = job.hourly_pay(p) * 6
    p.money += earned
    p.energy -= 25
    p.add_skill(job.skill, 3)
    if job.is_ra:
        p.ra_days += 1
        p.prof_favor += 1
    return f"6h shift at {job.name}. +${earned:.0f}, -25 energy, +3 {job.skill}"


def _gym_day(p: Player) -> str:
    p.health += 18
    p.energy -= 5
    return "Hit the USYD Sport gym + a long walk. +18 health, -5 energy"


def _study_grind(p: Player) -> str:
    # Boost the most-behind course
    weakest = min(p.courses, key=p.courses.get)
    p.add_course_progress(weakest, 12)
    p.energy -= 15
    p.health -= 3
    return f"Weekend grind on {weakest}. +12% there, -15 energy, -3 health"


WEEKEND_ACTIVITIES: List[WeekendActivity] = [
    WeekendActivity("rest",   "Rest day",        "Sleep in. Recover.",                     _rest_day),
    WeekendActivity("social", "Social outing",   "Newtown brunch with friends ($50).",     _social_outing),
    WeekendActivity("shift",  "Weekend shift",   "Pick up a 6h shift at your best job.",   _weekend_shift),
    WeekendActivity("gym",    "Gym + outdoors",  "USYD Sport gym + walk along Glebe.",     _gym_day),
    WeekendActivity("grind",  "Study grind",     "Lock in. Catch up on your weakest unit.", _study_grind),
]

WEEKEND_REGISTRY: Dict[str, WeekendActivity] = {a.key: a for a in WEEKEND_ACTIVITIES}
