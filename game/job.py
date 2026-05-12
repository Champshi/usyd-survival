"""
Job system — defines part-time jobs available to the player.

Each job links to a skill. As the player works, they gain skill;
higher skill unlocks better hourly pay. The Research Assistant (RA)
job is special — it counts toward the hidden "PhD scholarship" ending.

Demonstrates:
- Class hierarchy with shared interface
- @property for derived values
- Dictionary-based registry pattern
"""

from __future__ import annotations

from typing import Dict, List

from .player import Player


class Job:
    """A part-time job. Hourly pay scales with the player's skill."""

    def __init__(
        self,
        key: str,
        name: str,
        skill: str,
        base_pay: float,
        pay_per_skill: float,
        energy_cost_per_hour: float,
        unlock_week: int = 1,
        is_ra: bool = False,
    ) -> None:
        self.key = key
        self.name = name
        self.skill = skill                          # which skill this job grows
        self.base_pay = base_pay                    # AUD per hour at skill=0
        self.pay_per_skill = pay_per_skill          # extra AUD per skill point
        self.energy_cost_per_hour = energy_cost_per_hour
        self.unlock_week = unlock_week              # not available before this week
        self.is_ra = is_ra                          # marks the special RA job

    def hourly_pay(self, player: Player) -> float:
        """Pay rate scales linearly with the player's relevant skill."""
        return self.base_pay + self.pay_per_skill * player.skills[self.skill]

    def is_unlocked(self, player: Player) -> bool:
        return player.week >= self.unlock_week

    def work(self, player: Player, hours: int) -> str:
        """
        Player works this job for `hours` hours.
        Effects: +money, +skill, -energy. RA also bumps ra_days.
        """
        pay = self.hourly_pay(player) * hours
        player.money += pay
        player.energy -= self.energy_cost_per_hour * hours
        # Skill gain diminishes as you get better
        skill_gain = hours * (1.5 - player.skills[self.skill] / 100)
        player.add_skill(self.skill, skill_gain)
        if self.is_ra:
            player.ra_days += 1
            player.prof_favor += 1
        return f"Worked {hours}h at {self.name}: +${pay:.0f}, +{skill_gain:.1f} {self.skill}"


# ---------------------------------------------------------------------------
# Job registry
# ---------------------------------------------------------------------------

_JOBS: List[Job] = [
    Job("cafe", "Cafe waiter (King St)",  "service",  18, 0.30, 6),
    Job("tutor", "High-school tutor",     "teaching", 25, 0.40, 5, unlock_week=3),
    Job("dev", "Dev intern (Surry Hills)","coding",   30, 0.55, 7, unlock_week=5),
    Job("ra", "Research Assistant",        "research", 22, 0.45, 5, unlock_week=4, is_ra=True),
]

JOB_REGISTRY: Dict[str, Job] = {job.key: job for job in _JOBS}


def available_jobs(player: Player) -> List[Job]:
    """List comprehension: filter to jobs unlocked at the current week."""
    return [job for job in _JOBS if job.is_unlocked(player)]
