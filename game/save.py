"""
Save/load system using JSON files.

Demonstrates:
- File I/O (open/read/write)
- JSON serialization (json.dump / json.load)
- Exception handling for corrupted or missing saves
- pathlib for cross-platform paths
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .player import Player


SAVE_DIR = Path(__file__).resolve().parent.parent / "saves"
SAVE_FILE = SAVE_DIR / "savegame.json"


def save_game(player: Player) -> None:
    """Persist the player to disk as JSON. Creates the directory if needed."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(player.to_dict(), f, indent=2, ensure_ascii=False)
    except OSError as e:
        # Non-fatal: tell the player but don't crash the game
        player.log(f"  > [!] Save failed: {e}")


def load_game() -> Optional[Player]:
    """Try to load a saved game. Returns None on any failure."""
    if not SAVE_FILE.exists():
        return None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Player.from_dict(data)
    except (json.JSONDecodeError, KeyError, OSError):
        # Corrupted save — start fresh
        return None


def has_save() -> bool:
    return SAVE_FILE.exists()


def delete_save() -> None:
    """Remove the save file (e.g., after game over)."""
    if SAVE_FILE.exists():
        try:
            SAVE_FILE.unlink()
        except OSError:
            pass
