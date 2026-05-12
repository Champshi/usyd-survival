"""
Player module — defines the Player class that holds all game state.

The Player is the protagonist: a USYD postgrad CS student trying to
survive 13 weeks of classes + 2 weeks of exams while balancing energy,
money, health, and academic progress across 4 subjects.

Demonstrates the following advanced Python concepts:
- Object-oriented programming (class with state + behavior)
- Type hints (typing module)
- Dataclasses-like __init__ pattern
- Property-based stat clamping
- Dictionary comprehensions
"""

from __future__ import annotations

from typing import Dict, List


# Course codes — match Champ's actual semester schedule for thematic flavour
COURSES: List[str] = [
    "COMP9120",   # Database Systems
    "COMP9001",   # Python Programming
    "COMP9601",   # Computer Organization & Networks
    "INFO6007",   # IT Project Management
]

# Skill keys map to specific job types
SKILLS: List[str] = [
    "service",    # cafe / restaurant work
    "teaching",   # tutoring
    "coding",     # dev internships
    "research",   # research assistant (RA)
]


class Player:
    """The player character. Holds all mutable game state."""

    # ----- starting values (tuned for moderate difficulty) -----
    START_ENERGY = 80
    START_HEALTH = 100
    START_MONEY = 2000     # AUD — typical "first month" buffer
    START_ACADEMIC = 0     # academic progress per course (0-100)

    def __init__(self, name: str = "Student") -> None:
        self.name: str = name

        # ----- core stats (all clamped 0-100 except money) -----
        self._energy: float = self.START_ENERGY
        self._health: float = self.START_HEALTH
        self.money: float = self.START_MONEY  # can go negative => bankruptcy

        # ----- academic progress (0-100 per course) -----
        # Dict comprehension demonstrating an advanced concept
        self.courses: Dict[str, float] = {code: self.START_ACADEMIC for code in COURSES}

        # ----- final exam scores (filled in during exam weeks) -----
        self.exam_scores: Dict[str, float] = {code: 0.0 for code in COURSES}

        # ----- skills (0-100) — gained through working/studying -----
        self.skills: Dict[str, float] = {skill: 0.0 for skill in SKILLS}

        # ----- flags & counters for endings -----
        self.addiction_uses: int = 0      # count of stimulant uses
        self.ra_days: int = 0             # days spent as research assistant
        self.prof_favor: int = 0          # professor favourability score
        self.won_lottery: bool = False    # hidden ending trigger
        self.exam_phase: bool = False     # set True during exam weeks
        self.has_house: bool = True       # if False => "homeless"

        # ----- time tracking -----
        self.day: int = 1     # day-of-week 1..7 (1=Monday)
        self.week: int = 1    # week 1..15 (13 study + 2 exam)

        # ----- log of recent events for the UI -----
        self.event_log: List[str] = []

    # ----- clamped stat properties -----
    @property
    def energy(self) -> float:
        return self._energy

    @energy.setter
    def energy(self, value: float) -> None:
        self._energy = max(0.0, min(100.0, value))

    @property
    def health(self) -> float:
        return self._health

    @health.setter
    def health(self, value: float) -> None:
        self._health = max(0.0, min(100.0, value))

    # ----- helpers -----
    @property
    def total_day(self) -> int:
        """Day number from start of semester (1..105)."""
        return (self.week - 1) * 7 + self.day

    @property
    def is_weekend(self) -> bool:
        return self.day in (6, 7)

    @property
    def average_academic(self) -> float:
        return sum(self.courses.values()) / len(self.courses)

    @property
    def best_skill(self) -> str:
        return max(self.skills, key=self.skills.get)

    @property
    def best_skill_value(self) -> float:
        return self.skills[self.best_skill]

    def add_course_progress(self, course: str, amount: float) -> None:
        """Add progress to a specific course, clamped to [0, 100]."""
        if course not in self.courses:
            raise ValueError(f"Unknown course: {course}")
        self.courses[course] = max(0.0, min(100.0, self.courses[course] + amount))

    def add_skill(self, skill: str, amount: float) -> None:
        """Increase a skill, clamped to [0, 100]."""
        if skill not in self.skills:
            raise ValueError(f"Unknown skill: {skill}")
        self.skills[skill] = max(0.0, min(100.0, self.skills[skill] + amount))

    def log(self, message: str) -> None:
        """Add a message to the event log shown in the UI."""
        self.event_log.append(message)
        # Keep the log short so it fits in the UI panel
        if len(self.event_log) > 8:
            self.event_log = self.event_log[-8:]

    # ----- save / load support -----
    def to_dict(self) -> dict:
        """Serialize player state to a JSON-compatible dict."""
        return {
            "name": self.name,
            "energy": self._energy,
            "health": self._health,
            "money": self.money,
            "courses": self.courses,
            "exam_scores": self.exam_scores,
            "skills": self.skills,
            "addiction_uses": self.addiction_uses,
            "ra_days": self.ra_days,
            "prof_favor": self.prof_favor,
            "won_lottery": self.won_lottery,
            "exam_phase": self.exam_phase,
            "has_house": self.has_house,
            "day": self.day,
            "week": self.week,
            "event_log": self.event_log,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """Reconstruct a Player from a saved dict."""
        p = cls(name=data.get("name", "Student"))
        p._energy = data["energy"]
        p._health = data["health"]
        p.money = data["money"]
        p.courses = data["courses"]
        p.exam_scores = data["exam_scores"]
        p.skills = data["skills"]
        p.addiction_uses = data["addiction_uses"]
        p.ra_days = data["ra_days"]
        p.prof_favor = data["prof_favor"]
        p.won_lottery = data["won_lottery"]
        p.exam_phase = data["exam_phase"]
        p.has_house = data["has_house"]
        p.day = data["day"]
        p.week = data["week"]
        p.event_log = data.get("event_log", [])
        return p
