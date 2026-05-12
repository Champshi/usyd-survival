"""
USYD Survival Simulator
=======================
A text-based life simulation game where you play a USYD postgraduate student
trying to balance academics, finances, and health across one full semester.

Entry point — run this file to play:
    python main.py

Author: Champ
Course: COMP9001 — Python Programming
"""

from game.engine import GameEngine


def main() -> None:
    engine = GameEngine()
    engine.run()


if __name__ == "__main__":
    main()
