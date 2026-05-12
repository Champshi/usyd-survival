"""
Ending evaluation — 9 endings depending on the player's state.

Two kinds of endings:
  - "Game over" endings that trigger mid-semester (health=0, bankrupt, addict)
  - "Final" endings evaluated after exam week 15

Demonstrates:
- Enum-style class constants
- Conditional branching with priority ordering
- Polymorphism: each ending is a callable that produces flavour text
"""

from __future__ import annotations

from typing import Optional

from .player import Player


# Ending IDs — used for save files & the credits screen
class EndingId:
    HONOURS    = "honours"        # 学神
    WORK_KING  = "work_king"      # 打工皇帝
    NORMAL     = "normal"         # 普通毕业
    BANKRUPT   = "bankrupt"       # 破产
    DROPOUT    = "dropout"        # 退学
    HEAVEN     = "heaven"         # 天堂
    LOTTERY    = "lottery"        # 彩票中奖
    PHD        = "phd"            # 全奖直博
    ADDICT     = "addict"         # 瘾君子


ENDING_TITLES = {
    EndingId.HONOURS:   "ENDING 1/9 — Top of the Class (Honours)",
    EndingId.WORK_KING: "ENDING 2/9 — King of the Side Hustle",
    EndingId.NORMAL:    "ENDING 3/9 — You Did It (Pass)",
    EndingId.BANKRUPT:  "ENDING 4/9 — Bankrupt on King St",
    EndingId.DROPOUT:   "ENDING 5/9 — Withdrawn",
    EndingId.HEAVEN:    "ENDING 6/9 — Lights Out",
    EndingId.LOTTERY:   "HIDDEN ENDING 7/9 — A Winning Ticket",
    EndingId.PHD:       "HIDDEN ENDING 8/9 — Full Scholarship PhD",
    EndingId.ADDICT:    "BAD ENDING 9/9 — Lost in the Haze",
}


ENDING_TEXTS = {
    EndingId.HONOURS: """
You graduate with First Class Honours. Your name is read out at the ceremony in
the Great Hall. The Vice-Chancellor shakes your hand. Your parents are crying.
You stayed healthy, stayed solvent, and crushed every exam.
You are the student your tutor will never forget.
    """,
    EndingId.WORK_KING: """
Your part-time employer offers you a full-time, no-questions-asked role on the
spot. The pay is enough to make grad recruiters jealous. You graduate, sure —
but everyone knows your real degree was earned behind the counter and the
keyboard. You are the king of the side hustle.
    """,
    EndingId.NORMAL: """
You made it. Not glamorous, not headline-worthy — but you walk across the stage
with a degree, a healthy body, and a story to tell. Honestly? In a Sydney
postgrad CS program, that's already legendary. Pat yourself on the back.
    """,
    EndingId.BANKRUPT: """
The rent is overdue. The bank account is in the red. The IGA card got declined.
You pack a suitcase, drop out, and head to the airport. The semester ends
without you. You will tell yourself you'll come back. Maybe one day you will.
    """,
    EndingId.DROPOUT: """
The exam results come in. You missed the pass mark. The faculty letter is
polite but final: your enrolment has been suspended. You stand on Eastern
Avenue with a coffee that's already gone cold and a plan that no longer exists.
    """,
    EndingId.HEAVEN: """
Your housemate finds you collapsed at your desk, surrounded by half-finished
assignments and empty Red Bull cans. The paramedics are kind but quiet.
The semester carries on without you. Your tutor sends a sad email to the class.
There are some grades that aren't worth this.
    """,
    EndingId.LOTTERY: """
The numbers match. All of them.
You stare at your phone for a full minute before you understand.
You finish the semester anyway, just to prove a point. The degree is now a
souvenir. Tomorrow you fly business class to Tokyo. Some people are just lucky.
    """,
    EndingId.PHD: """
Your supervisor pulls you aside after lab on a Friday. She has secured a fully
funded PhD scholarship under her direct supervision. You will publish, teach,
and travel. Your name will be on papers. The work has paid off in the
most beautiful way possible. Welcome to academia.
    """,
    EndingId.ADDICT: """
You sit on the bench at Redfern station at 3am. Your exams are blurry memories.
Your phone is dead. Your wallet is empty. The pills are gone too, but the want
is still there, gnawing. Somewhere in another timeline, you graduated. Not
this one. The Sydney lights blink and the trains keep running, with or
without you.
    """,
}


# ---------------------------------------------------------------------------
# Ending evaluation
# ---------------------------------------------------------------------------

def check_instant_endings(player: Player) -> Optional[str]:
    """
    Endings that can fire any time during the semester.
    Order matters — first match wins.
    """
    if player.health <= 0:
        return EndingId.HEAVEN
    if player.money < -1000:
        return EndingId.BANKRUPT
    if player.addiction_uses >= 20:
        return EndingId.ADDICT
    if player.won_lottery:
        return EndingId.LOTTERY
    return None


def evaluate_final_ending(player: Player) -> str:
    """
    Evaluate the ending after the player has completed exams (week 15+).
    Order: hidden endings → honours → work king → pass/fail.
    """
    # Hidden lottery (also caught by instant check, but defensive)
    if player.won_lottery:
        return EndingId.LOTTERY

    average_exam = sum(player.exam_scores.values()) / len(player.exam_scores)
    all_passed = all(score >= 50 for score in player.exam_scores.values())

    # Hidden — full scholarship PhD
    if (
        player.ra_days >= 30
        and average_exam >= 80
        and player.prof_favor >= 30
        and all_passed
    ):
        return EndingId.PHD

    # Failed any exam — dropout
    if not all_passed:
        return EndingId.DROPOUT

    # Honours — top of the class
    if average_exam >= 85 and player.health >= 30:
        return EndingId.HONOURS

    # Work King — high skill mastered
    if player.best_skill_value >= 90 and all_passed:
        return EndingId.WORK_KING

    # Plain pass
    return EndingId.NORMAL


def get_ending_title(ending_id: str) -> str:
    return ENDING_TITLES.get(ending_id, "ENDING — ???")


def get_ending_text(ending_id: str) -> str:
    return ENDING_TEXTS.get(ending_id, "(no text)").strip()
