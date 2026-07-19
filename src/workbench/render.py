"""Branded rendering: ruby gradient wordmark and Rich rounded help panels.

The wordmark gradient is computed by hand (exact truecolor stops are part of the
brand contract and are asserted by tests); the panels and command tree are Rich,
matching the visual grammar of the Dotfiles CLI front door.
"""

from __future__ import annotations

import os
import sys
from typing import TextIO

from rich import box
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Typer >= 0.20 vendors click; the Typer* subclasses are the public-ish surface
# (same convention as the dotfiles CLI).
from typer._click.core import Command
from typer.core import TyperArgument, TyperGroup, TyperOption

WORKBENCH_BANNER = """\
██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
██║ █╗ ██║██║   ██║██████╔╝█████╔╝ ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
██║███╗██║██║   ██║██╔══██╗██╔═██╗ ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
 ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
"""
RUBY_STOPS = ((255, 184, 194), (230, 57, 86), (165, 9, 47), (101, 0, 24))

USAGE_ROOT = "workbench [OPTIONS] COMMAND [ARGS]..."
DESCRIPTION = "Portable agent intelligence: deploy and verify Claude Code and Codex configuration."
ALIAS_NOTE = "The shorter `wb` launcher is equivalent to `workbench`."
COMMANDS_PANEL = "Configuration — deploy, verify, and validate"


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
    """Render the Workbench wordmark with a horizontal ruby gradient."""
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
            red, green, blue = _gradient_color(column / max(1, width - 1), RUBY_STOPS)
            parts.append(f"\033[38;2;{red};{green};{blue}m{character}")
        rendered.append("".join(parts) + "\033[0m")
    return "\n".join(rendered)


def _console(stream: TextIO | None) -> Console:
    return Console(file=stream or sys.stdout)


def _error_panel(message: str) -> Panel:
    return Panel(
        Text.assemble(("×", "bold red"), "  ", message),
        title="Error",
        title_align="left",
        border_style="red",
        box=box.ROUNDED,
        padding=(0, 1),
    )


def _rows_table(rows: list[tuple[Text, Text]]) -> Table:
    table = Table.grid(padding=(0, 2))
    table.add_column(no_wrap=True)
    table.add_column(overflow="fold")
    for left, right in rows:
        table.add_row(left, right)
    return table


def _panel(title: str, rows: list[tuple[Text, Text]]) -> Panel:
    return Panel(
        _rows_table(rows), title=title, title_align="left", box=box.ROUNDED, padding=(0, 1)
    )


def _argument_choices(command: Command) -> list[str]:
    for param in command.params:
        choices = getattr(param.type, "choices", None)
        if isinstance(param, TyperArgument) and choices is not None:
            return [str(choice) for choice in choices]
    return []


def _options(command: Command) -> list[TyperOption]:
    return [
        param for param in command.params if isinstance(param, TyperOption) and param.name != "help"
    ]


def _command_rows(group: TyperGroup) -> list[tuple[Text, Text]]:
    """One row per command (with its vendor choices), option branches beneath."""
    rows: list[tuple[Text, Text]] = []
    for name, command in group.commands.items():
        label = name
        choices = _argument_choices(command)
        if choices:
            label += f" [{'|'.join(choices)}]"
        rows.append((Text(label, style="bold cyan"), Text(command.get_short_help_str(120))))
        options = _options(command)
        for index, option in enumerate(options):
            branch = "└" if index == len(options) - 1 else "├"
            rows.append(
                (
                    Text(f"  {branch} {option.opts[0]}", style="dim"),
                    Text(option.help or "", style="dim"),
                )
            )
    return rows


def print_help(
    group: TyperGroup, *, stream: TextIO | None = None, error: str | None = None
) -> None:
    """Render the branded front door in the same visual grammar as Dotfiles."""
    console = _console(stream)
    print(gradient_banner(), file=stream or sys.stdout)
    console.print()
    if error:
        console.print(_error_panel(error))
    console.print(Text.assemble((" Usage: ", "bold"), USAGE_ROOT))
    console.print()
    console.print(Padding(Text(DESCRIPTION), (0, 0, 0, 1)))
    console.print(Padding(Text(ALIAS_NOTE), (0, 0, 0, 1)))
    console.print()
    help_row = (Text("--help", style="bold cyan"), Text("Show this message and exit."))
    console.print(_panel("Options", [help_row]))
    console.print(_panel(COMMANDS_PANEL, _command_rows(group)))


def print_command_help(
    group: TyperGroup,
    command: str,
    *,
    stream: TextIO | None = None,
    error: str | None = None,
) -> None:
    """Render one command's contextual help (or contextual usage error)."""
    console = _console(stream)
    sub = group.commands[command]
    choices = _argument_choices(sub)
    options = _options(sub)
    usage = f"workbench {command}"
    if choices:
        usage += f" [{'|'.join(choices)}]"
    if options:
        usage += " [OPTIONS]"
    rows: list[tuple[Text, Text]] = []
    for param in sub.params:
        if isinstance(param, TyperArgument):
            rows.append((Text(param.name or "", style="bold cyan"), Text(param.help or "")))
    rows += [
        (Text(option.opts[0], style="bold cyan"), Text(option.help or "")) for option in options
    ]
    rows = rows or [(Text("no arguments"), Text(""))]
    if error:
        console.print(_error_panel(error))
    console.print(Text.assemble((" Usage: ", "bold"), usage))
    console.print()
    console.print(Padding(Text(sub.help or ""), (0, 0, 0, 1)))
    console.print()
    console.print(_panel("Arguments and options", rows))


def print_error(message: str, *, stream: TextIO | None = None) -> None:
    """Render a bare error panel (runtime failures outside the usage grammar)."""
    _console(stream).print(_error_panel(message))
