"""
Event system — random life events that hit the player throughout the semester.

Demonstrates:
- Class inheritance (Event base + GoodEvent/BadEvent/NeutralEvent subclasses)
- Polymorphism (apply() overridden per subclass)
- File I/O & JSON parsing
- The `random` module for weighted sampling
- List comprehensions for filtering eligible events
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Optional

from .player import Player


class Event:
    """Base class for a random event that can affect the player."""

    def __init__(
        self,
        eid: str,
        name: str,
        description: str,
        effects: Dict[str, float],
        weight: float = 1.0,
        min_week: int = 1,
        max_week: int = 99,
        weekday_only: bool = False,
        weekend_only: bool = False,
        choices: Optional[List[Dict]] = None,
    ) -> None:
        self.eid = eid
        self.name = name
        self.description = description
        self.effects = effects
        self.weight = weight
        self.min_week = min_week
        self.max_week = max_week
        self.weekday_only = weekday_only
        self.weekend_only = weekend_only
        self.choices = choices  # list of {label, effects} dicts, or None

    def is_eligible(self, player: Player) -> bool:
        """Check whether this event can fire given the player's current state."""
        if not (self.min_week <= player.week <= self.max_week):
            return False
        if self.weekday_only and player.is_weekend:
            return False
        if self.weekend_only and not player.is_weekend:
            return False
        return True

    def apply(self, player: Player) -> str:
        """Apply this event's effects to the player and return a description line."""
        _apply_effects(player, self.effects)
        return f"{self.icon()} {self.name} — {self.description}"

    def icon(self) -> str:
        """Override in subclasses for a coloured icon prefix."""
        return "[*]"


class GoodEvent(Event):
    def icon(self) -> str:
        return "[+]"


class BadEvent(Event):
    def icon(self) -> str:
        return "[-]"


class NeutralEvent(Event):
    def icon(self) -> str:
        return "[~]"


class HiddenEvent(Event):
    """Rare events that drive hidden endings (lottery, RA offer)."""

    def icon(self) -> str:
        return "[?]"


# ---------------------------------------------------------------------------
# Effect application
# ---------------------------------------------------------------------------

def _apply_effects(player: Player, effects: Dict[str, float]) -> None:
    """
    Apply a dict of stat-changes to the player.

    Recognised keys:
      energy, health, money, academic_avg, course:<CODE>, skill:<KEY>,
      addiction, ra_days, prof_favor, won_lottery
    """
    for key, value in effects.items():
        if key == "energy":
            player.energy += value
        elif key == "health":
            player.health += value
        elif key == "money":
            player.money += value
        elif key == "academic_avg":
            # Spread the change across all 4 courses evenly
            per_course = value / len(player.courses)
            for c in player.courses:
                player.add_course_progress(c, per_course)
        elif key.startswith("course:"):
            course_code = key.split(":", 1)[1]
            player.add_course_progress(course_code, value)
        elif key.startswith("skill:"):
            skill_key = key.split(":", 1)[1]
            player.add_skill(skill_key, value)
        elif key == "addiction":
            player.addiction_uses += int(value)
        elif key == "ra_days":
            player.ra_days += int(value)
        elif key == "prof_favor":
            player.prof_favor += int(value)
        elif key == "won_lottery":
            player.won_lottery = bool(value)


# ---------------------------------------------------------------------------
# Loading events from JSON
# ---------------------------------------------------------------------------

_EVENT_TYPE_MAP = {
    "good": GoodEvent,
    "bad": BadEvent,
    "neutral": NeutralEvent,
    "hidden": HiddenEvent,
}


def load_events(path: Path) -> List[Event]:
    """Load all events from a JSON file. Demonstrates File I/O + error handling."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Event database not found at {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Event database is malformed: {e}")

    events: List[Event] = []
    for item in raw:
        cls = _EVENT_TYPE_MAP.get(item.get("type", "neutral"), NeutralEvent)
        events.append(
            cls(
                eid=item["id"],
                name=item["name"],
                description=item["description"],
                effects=item.get("effects", {}),
                weight=item.get("weight", 1.0),
                min_week=item.get("min_week", 1),
                max_week=item.get("max_week", 99),
                weekday_only=item.get("weekday_only", False),
                weekend_only=item.get("weekend_only", False),
                choices=item.get("choices"),
            )
        )
    return events


# ---------------------------------------------------------------------------
# Event picker
# ---------------------------------------------------------------------------

class EventManager:
    """Selects random events that can fire on a given day."""

    def __init__(self, events: List[Event]) -> None:
        self.events = events

    def pick(self, player: Player) -> Optional[Event]:
        """Pick one weighted-random eligible event. Returns None if none fit."""
        # List comprehension: filter to eligible events
        eligible = [e for e in self.events if e.is_eligible(player)]
        if not eligible:
            return None
        weights = [e.weight for e in eligible]
        return random.choices(eligible, weights=weights, k=1)[0]
