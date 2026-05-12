"""
UI module — pixel-style terminal dashboard, built with the Rich library.

The screen is split into named regions and refreshed each turn:
  +-----------------------------------------------+
  |              HEADER (week + day)              |
  +----------------------+------------------------+
  |   CORE STATS         |   COURSES              |
  |   energy/money/health|   4 progress bars      |
  +----------------------+------------------------+
  |   SKILLS / FLAGS     |   EVENT LOG            |
  +----------------------+------------------------+

Demonstrates:
- Rich's Layout, Panel, Table, Live primitives
- f-strings + colour markup
- Helper functions for chunked progress-bar rendering
"""

from __future__ import annotations

import time
from typing import List, Optional

from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .player import COURSES, Player


console = Console()

# Pixel-style block characters used to draw progress bars
FULL_BLOCK = "█"
EMPTY_BLOCK = "░"
BAR_WIDTH = 14


# ---------------------------------------------------------------------------
# Title / banner
# ---------------------------------------------------------------------------

TITLE_BANNER = r"""
[bold magenta]
   _   _ ______   ___  ____    ____  _   _ ______     _____ _   _____ _    _____ _   _____ ____  _____
  | | | / ___\ \ / / _ \ / ___|  / ___|| | | |  _ \ \   /_   _\ \ / /_ _| | / / _ \ |  _ \  | |  / __ \
  | | | \___ \\ V / | | \___ \  \___ \| | | | |_) \ \ / / | |  \ V / | |  | |  | | | |_) |  | |  | | | |
  | |_| |___) || || |_| |___) |  ___) | |_| |  _ < \ V /  | |   | |  | |  | |_| | |  _ <   | |  | |_| |
   \___/|____/ |_| \___/|____/  |____/ \___/|_| \_\ \_/   |_|   |_| |___| \___/  |_| \_\  |_|   \___/
[/bold magenta]
[bold cyan]                            U S Y D   S U R V I V A L   S I M U L A T O R[/bold cyan]
[dim]                              A semester of pain, ramen, and academic glory.[/dim]
"""


def show_title() -> None:
    console.clear()
    # Smaller, cleaner title (the large ASCII above is decorative)
    title = Text()
    title.append("USYD SURVIVAL\n", style="bold magenta")
    title.append("      SIMULATOR\n", style="bold magenta")
    title.append("\n")
    title.append("A semester of pain, ramen, and academic glory.\n", style="dim italic")
    title.append("\n")
    title.append("Course: COMP9001  |  Built with Python + Rich\n", style="cyan")
    panel = Panel(
        Align.center(title, vertical="middle"),
        border_style="magenta",
        padding=(2, 4),
    )
    console.print(panel)


# ---------------------------------------------------------------------------
# Progress-bar primitives
# ---------------------------------------------------------------------------

def render_bar(value: float, maximum: float, color: str, width: int = BAR_WIDTH) -> Text:
    """Build a pixel-block progress bar as a Rich Text object."""
    if maximum <= 0:
        ratio = 0.0
    else:
        ratio = max(0.0, min(1.0, value / maximum))
    filled = int(round(ratio * width))
    bar = Text()
    bar.append(FULL_BLOCK * filled, style=color)
    bar.append(EMPTY_BLOCK * (width - filled), style="grey30")
    return bar


def stat_color(value: float) -> str:
    """Colour a stat green/yellow/red based on how healthy the value is."""
    if value >= 60:
        return "bright_green"
    if value >= 30:
        return "yellow"
    return "bright_red"


def money_color(money: float) -> str:
    if money >= 500:
        return "bright_green"
    if money >= 0:
        return "yellow"
    return "bright_red"


# ---------------------------------------------------------------------------
# Panels
# ---------------------------------------------------------------------------

def header_panel(player: Player) -> Panel:
    """Top header panel — shows week, day, semester progress."""
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_name = weekdays[player.day - 1] if 1 <= player.day <= 7 else "?"
    phase = "[bold red]EXAM WEEK[/bold red]" if player.exam_phase else "[cyan]Study Week[/cyan]"
    progress_bar = render_bar(player.total_day, 105, "bright_blue", width=40)

    table = Table.grid(expand=True)
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_row(
        f"[bold yellow]Week {player.week:2d}[/bold yellow]  [white]{day_name}[/white]   {phase}",
        f"[dim]Day {player.total_day:3d} / 105[/dim]",
    )
    return Panel(
        Group(table, progress_bar),
        title="[bold magenta]:: USYD Survival Sim ::[/bold magenta]",
        border_style="magenta",
    )


def stats_panel(player: Player) -> Panel:
    """Energy / Health / Money panel."""
    table = Table.grid(padding=(0, 1))
    table.add_column(width=7)
    table.add_column(width=BAR_WIDTH)
    table.add_column(justify="right", no_wrap=True)

    table.add_row(
        Text("Energy", style="bold"),
        render_bar(player.energy, 100, stat_color(player.energy)),
        f"[{stat_color(player.energy)}]{player.energy:3.0f}/100[/]",
    )
    table.add_row(
        Text("Health", style="bold"),
        render_bar(player.health, 100, stat_color(player.health)),
        f"[{stat_color(player.health)}]{player.health:3.0f}/100[/]",
    )
    money_bar = render_bar(max(0, player.money), 5000, money_color(player.money))
    table.add_row(
        Text("Money",  style="bold"),
        money_bar,
        f"[{money_color(player.money)}]${player.money:>5.0f}[/]",
    )
    return Panel(table, title="[bold cyan]Core Stats[/bold cyan]", border_style="cyan")


def courses_panel(player: Player) -> Panel:
    """Per-course academic progress."""
    table = Table.grid(padding=(0, 1))
    table.add_column(width=9)
    table.add_column(width=BAR_WIDTH)
    table.add_column(justify="right", no_wrap=True)
    for code in COURSES:
        progress = player.courses[code]
        color = stat_color(progress) if progress >= 50 else "yellow" if progress >= 30 else "bright_red"
        table.add_row(
            Text(code, style="bold"),
            render_bar(progress, 100, color),
            f"[{color}]{progress:5.1f}%[/]",
        )
    return Panel(table, title="[bold yellow]Courses[/bold yellow]", border_style="yellow")


def skills_panel(player: Player) -> Panel:
    """Skills + flags panel."""
    table = Table.grid(padding=(0, 1))
    table.add_column(width=9)
    table.add_column(width=BAR_WIDTH)
    table.add_column(justify="right", no_wrap=True)
    for skill, val in player.skills.items():
        table.add_row(
            Text(skill.title(), style="bold"),
            render_bar(val, 100, "bright_magenta"),
            f"[bright_magenta]{val:5.1f}[/]",
        )

    flag_lines = []
    if player.addiction_uses > 0:
        color = "red" if player.addiction_uses >= 10 else "yellow"
        flag_lines.append(f"[{color}]Addiction: {player.addiction_uses}[/]")
    if player.ra_days > 0:
        flag_lines.append(f"[bright_blue]RA days: {player.ra_days}[/]")
    if player.prof_favor > 0:
        flag_lines.append(f"[bright_green]Prof favour: {player.prof_favor}[/]")
    if player.won_lottery:
        flag_lines.append("[bold yellow]LOTTERY WINNER[/]")

    flag_text = Text.from_markup(" | ".join(flag_lines)) if flag_lines else Text("(no flags yet)", style="dim")
    return Panel(Group(table, flag_text), title="[bold magenta]Skills & Flags[/bold magenta]", border_style="magenta")


def event_log_panel(player: Player) -> Panel:
    """Event log panel — last 8 events."""
    if not player.event_log:
        body = Text("No events yet.", style="dim italic")
    else:
        body = Text("\n".join(player.event_log))
    return Panel(body, title="[bold green]Event Log[/bold green]", border_style="green")


# ---------------------------------------------------------------------------
# Full dashboard
# ---------------------------------------------------------------------------

def build_dashboard(player: Player) -> Layout:
    """Compose the full dashboard layout for one frame."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="middle", ratio=1),
        Layout(name="bottom", ratio=1),
    )
    layout["header"].update(header_panel(player))
    layout["middle"].split_row(
        Layout(stats_panel(player), name="stats"),
        Layout(courses_panel(player), name="courses"),
    )
    layout["bottom"].split_row(
        Layout(skills_panel(player), name="skills"),
        Layout(event_log_panel(player), name="log"),
    )
    return layout


def show_dashboard(player: Player) -> None:
    """Static one-shot render of the dashboard."""
    console.clear()
    console.print(build_dashboard(player), height=28)


def animate_transition(player: Player, ticks: int = 6, delay: float = 0.06) -> None:
    """Brief 'animated' refresh — gives the UI a sense of motion between turns."""
    with Live(build_dashboard(player), console=console, refresh_per_second=20, screen=False) as live:
        for _ in range(ticks):
            time.sleep(delay)
            live.update(build_dashboard(player))


# ---------------------------------------------------------------------------
# Coloured helpers for the rest of the game
# ---------------------------------------------------------------------------

def info(message: str) -> None:
    console.print(f"[cyan]> {message}[/cyan]")


def warn(message: str) -> None:
    console.print(f"[bold yellow]! {message}[/bold yellow]")


def error(message: str) -> None:
    console.print(f"[bold red]X {message}[/bold red]")


def big_announce(message: str, color: str = "magenta") -> None:
    console.print(Panel(Text(message, justify="center"), border_style=color, padding=(1, 4)))


def prompt(message: str, default: Optional[str] = None) -> str:
    """Wrapped input() — Rich-coloured prompt."""
    suffix = f" [{default}]" if default else ""
    raw = console.input(f"[bold cyan]?[/bold cyan] {message}{suffix} > ").strip()
    return raw if raw else (default or "")
