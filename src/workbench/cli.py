"""Typer command surface and branded help routing for the workbench CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
import typer.main
from typer._click import exceptions as click_exceptions
from typer.core import TyperGroup

from workbench import drift as drift_module
from workbench import lint as lint_module
from workbench.core import WorkbenchError, _vendors
from workbench.render import DESCRIPTION, print_command_help, print_error, print_help
from workbench.sync import sync_claude, sync_codex


class Vendor(StrEnum):
    CLAUDE = "claude"
    CODEX = "codex"
    ALL = "all"


app = typer.Typer(
    name="workbench",
    help=DESCRIPTION,
    add_completion=False,
)


def _home() -> Path:
    return Path(os.environ.get("WORKBENCH_HOME", Path.home()))


@app.command(short_help="deploy canonical configuration")
def sync(
    vendor: Annotated[
        Vendor, typer.Argument(help="vendor to reconcile (default: all)")
    ] = Vendor.ALL,
    no_skills: Annotated[
        bool, typer.Option("--no-skills", help="skip shared-skill installation")
    ] = False,
    no_plugins: Annotated[
        bool, typer.Option("--no-plugins", help="skip declared-plugin installation")
    ] = False,
) -> None:
    """Deploy Workbench-managed configuration to one or both vendors."""
    home = _home()
    for name in _vendors(vendor.value):
        deploy = sync_claude if name == "claude" else sync_codex
        deploy(home, deploy_skills=not no_skills, deploy_plugins=not no_plugins)
    print("OK workbench synchronized")


@app.command(short_help="report managed drift and external additions")
def drift(
    vendor: Annotated[Vendor, typer.Argument(help="vendor to inspect (default: all)")] = Vendor.ALL,
    no_plugins: Annotated[
        bool, typer.Option("--no-plugins", help="skip declared-plugin verification")
    ] = False,
) -> int:
    """Compare live vendor configuration directly with canonical Workbench sources."""
    return drift_module.drift(_home(), _vendors(vendor.value), verify_plugins=not no_plugins)


@app.command(short_help="validate canonical repository sources")
def lint() -> int:
    """Validate skills, local links, JSON, TOML, and shell syntax."""
    return lint_module.lint()


def main(argv: list[str] | None = None) -> int:
    command = typer.main.get_command(app)
    assert isinstance(command, TyperGroup)  # the top-level app is always a group
    raw_argv = sys.argv[1:] if argv is None else argv
    if not raw_argv or raw_argv in (["-h"], ["--help"]):
        print_help(command)
        return 0
    requested = next((value for value in raw_argv if value in command.commands), None)
    if requested and any(value in {"-h", "--help"} for value in raw_argv):
        print_command_help(command, requested)
        return 0
    try:
        result = command.main(args=raw_argv, prog_name="workbench", standalone_mode=False)
    except click_exceptions.Exit as exc:  # a stray --help click handled itself
        return int(exc.exit_code)
    except click_exceptions.UsageError as exc:
        message = exc.format_message()
        if requested:
            print_command_help(command, requested, stream=sys.stderr, error=message)
        else:
            print_help(command, stream=sys.stderr, error=message)
        return 2
    except (WorkbenchError, OSError, subprocess.CalledProcessError) as exc:
        print_error(str(exc), stream=sys.stderr)
        if requested:
            print_command_help(command, requested, stream=sys.stderr)
        return 1
    return result if isinstance(result, int) else 0


def entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":  # pragma: no cover
    entry()
