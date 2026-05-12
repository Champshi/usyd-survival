"""
Exam-week mechanics.

During weeks 14-15 the game switches into exam mode. Each course has a final
exam whose score is a function of:
  - Course progress (the dominant factor)
  - Player's energy at exam time (rested students score higher)
  - Player's health
  - A little random luck

A score < 50 = fail = dropout ending. A high score across all four courses
opens up Honours / PhD endings.
"""

from __future__ import annotations

import random
from typing import Dict

from .player import COURSES, Player


def calculate_exam_score(player: Player, course: str) -> float:
    """Compute one course's final exam score."""
    base = player.courses[course]
    # Energy modifier: 0.7x exhausted -> 1.2x rested
    energy_mod = 0.7 + (player.energy / 100) * 0.5
    # Health modifier: 0.8x sick -> 1.1x healthy
    health_mod = 0.8 + (player.health / 100) * 0.3
    # Random luck factor — exam day variance
    luck = random.uniform(-5, 5)

    score = base * energy_mod * health_mod + luck
    return max(0.0, min(100.0, score))


def run_exams(player: Player) -> Dict[str, float]:
    """
    Run all four final exams. Each exam costs energy/health.
    Stores results back on the player and returns a dict of scores.
    """
    results: Dict[str, float] = {}
    for course in COURSES:
        score = calculate_exam_score(player, course)
        player.exam_scores[course] = score
        results[course] = score
        # Each exam is exhausting
        player.energy -= 15
        player.health -= 3
    return results
