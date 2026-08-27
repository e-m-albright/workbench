"""Workbench branding and runtime-error rendering."""

from __future__ import annotations

import os
import sys
from typing import TextIO

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

WORKBENCH_BANNER = """\
██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
██║ █╗ ██║██║   ██║██████╔╝█████╔╝ ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
██║███╗██║██║   ██║██╔══██╗██╔═██╗ ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
 ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
"""
LICHEN_ENAMEL_STOPS = (
    (238, 230, 189),
    (196, 197, 133),
    (140, 160, 111),
    (101, 126, 104),
    (80, 102, 95),
    (57, 78, 82),
)

DESCRIPTION = (
    "Portable agent intelligence: deploy and verify Pi, Claude Code, and Codex configuration."
)
ALIAS_NOTE = "The shorter `wb` launcher is equivalent to `workbench`."


def _gradient_color(
    position: float, stops: tuple[tuple[int, int, int], ...]
) -> tuple[int, int, int]:
    position = min(max(position, 0.0), 1.0)
    segment = position * (len(stops) - 1)
    index = min(int(segment), len(stops) - 2)
    fraction = segment - index
    start, end = stops[index], stops[index + 1]

    def mix(channel: int) -> int:
        return round(start[channel] + (end[channel] - start[channel]) * fraction)

    return (mix(0), mix(1), mix(2))


def gradient_banner(*, color: bool | None = None) -> str:
    """Render the Workbench wordmark with the Lichen Enamel gradient."""
    lines = WORKBENCH_BANNER.rstrip().splitlines()
    if color is None:
        color = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    if not color:
        return "\n".join(lines)
    width = max(map(len, lines))
    rendered: list[str] = []
    for line in lines:
        parts: list[str] = []
        for column, character in enumerate(line):
            red, green, blue = _gradient_color(1 - column / max(1, width - 1), LICHEN_ENAMEL_STOPS)
            parts.append(f"\033[38;2;{red};{green};{blue}m{character}")
        rendered.append("".join(parts) + "\033[0m")
    return "\n".join(rendered)


def print_error(message: str, *, stream: TextIO | None = None) -> None:
    """Render a runtime failure outside Typer's native usage grammar."""
    Console(file=stream or sys.stderr).print(
        Panel(
            Text.assemble(("×", "bold red"), "  ", message),
            title="Error",
            title_align="left",
            border_style="red",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )
