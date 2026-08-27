"""Typer command surface and branded help routing for the workbench CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from typer._click.core import Context
from typer._click.formatting import HelpFormatter
from typer.core import TyperGroup

from workbench import drift as drift_module
from workbench import lint as lint_module
from workbench.core import VENDOR_CHOICES, WorkbenchError, _vendors, drain_changed_paths
from workbench.render import ALIAS_NOTE, DESCRIPTION, gradient_banner, print_error
from workbench.sync import sync_claude, sync_codex, sync_pi, sync_rules


class Vendor(StrEnum):
    CLAUDE = "claude"
    CODEX = "codex"
    PI = "pi"
    ALL = "all"


# The Typer choice enum and core's vendor list must never diverge; a dynamic
# StrEnum would guarantee that but defeats static checking, so assert instead.
assert tuple(member.value for member in Vendor) == VENDOR_CHOICES

COMMANDS_PANEL = "Configuration — deploy, verify, and validate"


class BrandedGroup(TyperGroup):
    """Add the wordmark, then delegate help rendering entirely to Typer."""

    def format_help(self, ctx: Context, formatter: HelpFormatter) -> None:
        print(gradient_banner())
        super().format_help(ctx, formatter)


app = typer.Typer(
    cls=BrandedGroup,
    name="workbench",
    help=f"{DESCRIPTION}\n\n{ALIAS_NOTE}",
    add_completion=False,
)


def _home() -> Path:
    return Path(os.environ.get("WORKBENCH_HOME", Path.home()))


@app.command(short_help="deploy canonical configuration", rich_help_panel=COMMANDS_PANEL)
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
    rules_only: Annotated[
        bool, typer.Option("--rules-only", help="deploy only global instruction files")
    ] = False,
) -> None:
    """Deploy Workbench-managed configuration to supported coding agents."""
    home = _home()
    deployers = {"claude": sync_claude, "codex": sync_codex, "pi": sync_pi}
    drain_changed_paths()
    for name in _vendors(vendor.value):
        if rules_only:
            sync_rules(home, name)
            continue
        deployers[name](
            home,
            deploy_skills=not no_skills,
            deploy_plugins=not no_plugins,
        )
    changed = drain_changed_paths()
    for path in changed:
        try:
            print(f"updated ~/{path.relative_to(home)}")
        except ValueError:
            print(f"updated {path}")
    if changed:
        print(f"OK workbench synchronized; {len(changed)} file(s) updated")
    else:
        print("OK workbench synchronized; nothing to change")


@app.command(
    short_help="report managed drift and external additions", rich_help_panel=COMMANDS_PANEL
)
def drift(
    vendor: Annotated[Vendor, typer.Argument(help="vendor to inspect (default: all)")] = Vendor.ALL,
    no_plugins: Annotated[
        bool, typer.Option("--no-plugins", help="skip declared-plugin verification")
    ] = False,
) -> int:
    """Compare live vendor configuration directly with canonical Workbench sources."""
    return drift_module.drift(_home(), _vendors(vendor.value), verify_plugins=not no_plugins)


@app.command(short_help="validate canonical repository sources", rich_help_panel=COMMANDS_PANEL)
def lint() -> int:
    """Validate skills, local links, JSON, TOML, and shell syntax."""
    return lint_module.lint()


def main(argv: list[str] | None = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else argv
    if not raw_argv:
        raw_argv = ["--help"]
    try:
        app(args=raw_argv, prog_name="workbench", standalone_mode=True)
    except SystemExit as error:
        return int(error.code or 0)
    except (WorkbenchError, OSError, subprocess.CalledProcessError) as error:
        print_error(str(error), stream=sys.stderr)
        return 1
    return 0


def entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":  # pragma: no cover
    entry()
