"""Small, explicit deployment profiles for personal and managed-work hosts."""

from __future__ import annotations

from typing import Literal

from workbench.core import AGENTS

Profile = Literal["personal", "work"]

WORK_PI = AGENTS / "profiles/work/pi"
WORK_PI_EXTENSIONS = {
    "activity-title.ts",
    "footer.ts",
    "permission-policy.ts",
    "presets.ts",
    "safe-git.ts",
    "welcome.ts",
    "worker.ts",
    "workspace-files.ts",
}
WORK_SKILL_EXCLUDES = {"paseo-management"}


def vendors(profile: Profile, selected: tuple[str, ...]) -> tuple[str, ...]:
    """Limit the work profile to its approved Claude and Pi harnesses."""
    if profile == "personal":
        return selected
    return tuple(vendor for vendor in selected if vendor in {"claude", "pi"})
