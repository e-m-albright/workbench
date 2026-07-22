from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from workbench import codex, core, mcp, render, sync
from workbench import drift as drift_mod
from workbench import lint as lint_mod


class WorkbenchTests(unittest.TestCase):
    def run_hook(self, name: str, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(core.AGENTS / "shared/hooks" / name)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

    def deploy_skills(self, home: Path, *roots: str) -> None:
        for root in roots:
            for source in core.AGENTS.glob("skills/*"):
                if source.is_dir() and (source / "SKILL.md").exists():
                    shutil.copytree(source, home / root / source.name)

    def test_merge_mcp_preserves_external_and_removes_tombstones(self) -> None:
        merged = mcp.merge_mcp(
            {
                "external": {"command": "example"},
                "context7": {"command": "retired"},
                "granola": {"url": "stale"},
            },
            "claude",
        )

        self.assertEqual(merged["external"], {"command": "example"})
        self.assertNotIn("context7", merged)
        self.assertEqual(merged["granola"]["url"], "https://mcp.granola.ai/mcp")

    def test_merge_mcp_prunes_managed_server_removed_from_target(self) -> None:
        merged = mcp.merge_mcp(
            {
                "granola": {"url": "https://mcp.granola.ai/mcp"},
                "computer-use": {"command": "app-owned"},
            },
            "codex",
        )

        self.assertNotIn("granola", merged)
        self.assertEqual(merged["computer-use"], {"command": "app-owned"})

    def test_invalid_json_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "settings.json"
            path.write_text("{")

            with self.assertRaises(core.WorkbenchError):
                core.load_json(path, {})

            self.assertEqual(path.read_text(), "{")

    def test_write_text_keeps_one_backup(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "config.json"
            path.write_text("old")

            self.assertTrue(core.write_text(path, "new"))

            self.assertEqual(path.read_text(), "new")
            self.assertEqual(path.with_name("config.json.bak").read_text(), "old")

    def test_launcher_resolves_chained_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            link = Path(raw) / "workbench"
            link.symlink_to(core.ROOT / "bin/workbench")
            chained = Path(raw) / "wb"
            chained.symlink_to(link)

            result = subprocess.run(
                [str(chained), "lint"], capture_output=True, text=True, check=False
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout, r"OK \d+ skills")

    def test_bare_launcher_renders_branded_complete_command_tree(self) -> None:
        result = subprocess.run(
            [str(core.ROOT / "bin/workbench")],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("██╗    ██╗", result.stdout)
        self.assertIn("Usage: workbench [OPTIONS] COMMAND [ARGS]...", result.stdout)
        self.assertIn("Options", result.stdout)
        self.assertIn("Configuration — deploy, verify, and validate", result.stdout)
        self.assertIn("sync [claude|codex|pi|all]", result.stdout)
        self.assertIn("drift [claude|codex|pi|all]", result.stdout)
        self.assertIn("--no-skills", result.stdout)

    def test_banner_uses_ruby_truecolor_gradient_on_terminals(self) -> None:
        rendered = render.gradient_banner(color=True)

        self.assertIn("\033[38;2;255;184;194m", rendered)
        self.assertIn("\033[38;2;101;0;24m", rendered)
        self.assertTrue(rendered.endswith("\033[0m"))

    def test_bare_just_uses_dotfiles_heading_convention(self) -> None:
        result = subprocess.run(
            ["just"], cwd=core.ROOT, capture_output=True, text=True, check=False
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("workbench CLI", result.stdout)
        self.assertIn("dev tasks (cwd: repository root)", result.stdout)
        self.assertIn("[quality]", result.stdout)
        self.assertIn("[testing]", result.stdout)
        self.assertIn("[deployment]", result.stdout)

    def test_sync_help_explains_targets_and_optional_installers(self) -> None:
        result = subprocess.run(
            [str(core.ROOT / "bin/workbench"), "sync", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("claude|codex|pi|all", result.stdout)
        self.assertIn("--no-skills", result.stdout)
        self.assertIn("--no-plugins", result.stdout)

    def test_every_command_has_contextual_visual_help(self) -> None:
        expectations = {
            "sync": "--no-plugins",
            "drift": "default: all",
            "lint": "shell syntax",
        }
        for command, expected in expectations.items():
            with self.subTest(command=command):
                result = subprocess.run(
                    [str(core.ROOT / "bin/workbench"), command, "--help"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"workbench {command}", result.stdout)
                self.assertIn("Arguments and options", result.stdout)
                self.assertIn(expected, result.stdout)
                self.assertNotIn("usage: workbench", result.stderr)

    def test_invalid_target_has_visual_contextual_error(self) -> None:
        result = subprocess.run(
            [str(core.ROOT / "bin/workbench"), "sync", "other"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("╭─ Error", result.stderr)
        self.assertIn("is not one of 'claude', 'codex',", result.stderr)
        self.assertIn("workbench sync [claude|codex|pi|all]", result.stderr)
        self.assertNotIn("usage: workbench", result.stderr)

    def test_unknown_command_has_visual_registry_error(self) -> None:
        result = subprocess.run(
            [str(core.ROOT / "bin/workbench"), "other"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("╭─ Error", result.stderr)
        self.assertIn("No such command 'other'", result.stderr)
        self.assertIn("Configuration", result.stderr)
        self.assertNotIn("usage: workbench", result.stderr)

    @patch.object(subprocess, "run")
    @patch.object(shutil, "which", return_value="/usr/bin/npx")
    def test_skill_sync_removes_retired_skills_before_installing(self, _which, run) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            for name in core.RETIRED_SKILLS:
                retired = home / ".agents/skills" / name
                retired.mkdir(parents=True)
                (retired / "SKILL.md").write_text("retired")

            sync._sync_skills("codex", home)

            for name in core.RETIRED_SKILLS:
                self.assertFalse((home / ".agents/skills" / name).exists())

        remove_command = run.call_args_list[0].args[0]
        self.assertEqual(remove_command[:3], ["npx", core.SKILLS_CLI, "remove"])
        self.assertIn("agentic-e2e-debugging", remove_command)
        self.assertIn("converge", remove_command)

    def test_check_treats_retired_deployed_skill_as_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill_root = Path(raw)
            retired = skill_root / "converge"
            retired.mkdir()
            (retired / "SKILL.md").write_text("retired")
            findings: list[str] = []
            external: list[str] = []

            drift_mod._check_skills(skill_root, "codex", findings, external)

            self.assertIn("DRIFT retired codex skill still present: converge", findings)
            self.assertNotIn("EXTERNAL codex skill: converge", external)

    def test_skill_descriptions_fit_context_budget(self) -> None:
        descriptions = []
        for skill in core.AGENTS.glob("skills/*/SKILL.md"):
            match = re.search(r"^description:\s*([^\n]+)$", skill.read_text(), re.MULTILINE)
            self.assertIsNotNone(match, skill)
            assert match
            raw = match.group(1).strip()
            self.assertFalse(": " in raw and not raw.startswith('"'), skill)
            descriptions.append(raw.strip('"'))

        self.assertTrue(all(len(description) <= 280 for description in descriptions))
        self.assertLessEqual(sum(map(len, descriptions)), 5_000)

    def test_markdown_link_check_skips_examples_and_finds_broken_links(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "ok.md").write_text("ok")
            (root / "links.md").write_text(
                "[ok](ok.md)\n[missing](missing.md)\n```md\n[example](fake.md)\n```\n"
            )

            errors = lint_mod._markdown_link_errors(root)

            self.assertEqual(len(errors), 1)
            self.assertIn("missing.md", errors[0])

    def test_repository_markdown_links_resolve(self) -> None:
        self.assertEqual(lint_mod._markdown_link_errors(core.ROOT), [])

    def test_sync_claude_preserves_unmanaged_settings(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            settings = home / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(json.dumps({"custom": 7, "permissions": {"custom": True}}))

            sync.sync_claude(home, deploy_skills=False)

            actual = json.loads(settings.read_text())
            self.assertEqual(actual["custom"], 7)
            self.assertTrue(actual["permissions"]["custom"])
            self.assertIn("enabledPlugins", actual)
            self.assertEqual(actual["defaultMode"], "auto")
            self.assertNotIn("defaultMode", actual["permissions"])
            self.assertTrue(actual["sandbox"]["enabled"])
            self.assertTrue(actual["sandbox"]["allowUnsandboxedCommands"])
            self.assertIn("git push *", actual["sandbox"]["excludedCommands"])
            self.assertTrue((home / ".claude.json.bak").exists() is False)

    def test_plugin_inventory_parses_each_vendor_shape_with_enabled_state(
        self,
    ) -> None:
        claude = json.dumps(
            [
                {"id": "example@market", "enabled": True},
                {"id": "dormant@market", "enabled": False},
            ]
        )
        codex = json.dumps({"installed": [{"pluginId": "example@market", "enabled": True}]})

        self.assertEqual(
            core._installed_plugins("claude", claude),
            {"example@market": True, "dormant@market": False},
        )
        self.assertEqual(core._installed_plugins("codex", codex), {"example@market": True})

    @patch.object(drift_mod, "_plugin_inventory")
    def test_check_plugins_requires_enabled_and_reports_external(self, inventory) -> None:
        declared = core._string_array(core.AGENTS / "claude/plugins.json")
        inventory.return_value = {
            **dict.fromkeys(declared, True),
            declared[0]: False,
            "extra@market": True,
        }
        findings: list[str] = []
        external: list[str] = []

        drift_mod._check_plugins("claude", Path("/nonexistent"), findings, external)

        self.assertEqual(findings, [f"DRIFT claude plugin disabled: {declared[0]}"])
        self.assertEqual(external, ["EXTERNAL claude plugin: extra@market"])

    @patch.object(shutil, "which", return_value=None)
    def test_check_plugins_degrades_when_cli_is_missing(self, _which) -> None:
        findings: list[str] = []
        external: list[str] = []

        drift_mod._check_plugins("claude", Path("/nonexistent"), findings, external)

        self.assertEqual(findings, [])
        self.assertEqual(external, ["NOTE claude plugins unverified (CLI not found)"])

    def test_codex_connector_plugins_are_declared(self) -> None:
        plugins = core._string_array(core.AGENTS / "codex/plugins.json")

        self.assertEqual(
            plugins,
            [
                "gmail@openai-curated",
                "google-calendar@openai-curated",
                "granola@openai-curated",
            ],
        )
        self.assertNotIn("granola", mcp.active_mcp("codex"))

    def test_sync_removes_retired_workbench_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            hook_dir = home / core.DATA_REL / "hooks"
            hook_dir.mkdir(parents=True)
            retired = hook_dir / "notify.sh"
            retired.write_text("#!/bin/sh\n")
            backup = hook_dir / "notify.sh.bak"
            backup.write_text("#!/bin/sh\n")

            sync.sync_claude(home, deploy_skills=False)

            self.assertFalse(retired.exists())
            self.assertFalse(backup.exists())
            self.assertTrue((hook_dir / "guard-destructive-shell.sh").exists())

    def test_codex_subagents_render_as_native_toml(self) -> None:
        source = core.AGENTS / "subagents/code-reviewer.md"

        rendered = codex._render_codex_subagent(source)
        parsed = tomllib.loads(rendered)

        self.assertEqual(parsed["name"], "code-reviewer")
        self.assertIn("correctness", parsed["description"])
        self.assertIn("review", parsed["developer_instructions"].lower())

    def test_sync_codex_replaces_markdown_subagents_and_prunes_retired(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / ".codex/agents"
            destination.mkdir(parents=True)
            (destination / "code-reviewer.md").write_text("stale")
            (destination / "docs-scribe.md").write_text("retired")

            sync._sync_subagents("codex", destination)

            self.assertFalse(list(destination.glob("*.md*")))
            self.assertFalse((destination / "docs-scribe.toml").exists())
            parsed = tomllib.loads((destination / "code-reviewer.toml").read_text())
            self.assertEqual(parsed["name"], "code-reviewer")

    def test_check_detects_managed_file_content_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            sync.sync_claude(home, deploy_skills=False)
            self.deploy_skills(home, ".claude/skills")

            self.assertEqual(drift_mod.drift(home, ("claude",), verify_plugins=False), 0)

            (home / ".claude/hooks.json").write_text("{}\n")
            (home / ".claude/settings.json").write_text(json.dumps({"voiceEnabled": False}))

            self.assertEqual(drift_mod.drift(home, ("claude",), verify_plugins=False), 1)

    def test_drift_ignores_sync_backup_of_current_hook(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            sync.sync_claude(home, deploy_skills=False)
            self.deploy_skills(home, ".claude/skills")
            backup = home / core.DATA_REL / "hooks/guard-destructive-shell.sh.bak"
            backup.write_text("#!/bin/sh\n")

            self.assertEqual(drift_mod.drift(home, ("claude",), verify_plugins=False), 0)

    @patch.object(drift_mod.shutil, "which", return_value="/usr/local/bin/pi")
    def test_temporary_home_sync_and_check_all_vendors(self, _which) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            sync.sync_claude(home, deploy_skills=False, deploy_plugins=False)
            sync.sync_codex(home, deploy_skills=False, deploy_plugins=False)
            sync.sync_pi(home, deploy_skills=True, deploy_plugins=False)
            self.deploy_skills(home, ".claude/skills")

            self.assertEqual(
                drift_mod.drift(home, ("claude", "codex", "pi"), verify_plugins=False),
                0,
            )

    @patch.object(drift_mod.shutil, "which", return_value="/usr/local/bin/pi")
    def test_pi_sync_preserves_external_state_and_detects_managed_drift(self, _which) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            pi_home = home / ".pi/agent"
            (pi_home / "extensions").mkdir(parents=True)
            (pi_home / "sessions/project").mkdir(parents=True)
            session = pi_home / "sessions/project/session.jsonl"
            session.write_text("private conversation\n")
            session.chmod(0o644)
            (pi_home / "skills/external-skill").mkdir(parents=True)
            (pi_home / "skills/external-skill/SKILL.md").write_text(
                "---\nname: external-skill\ndescription: external\n---\n"
            )
            canonical_name = next(
                path.parent.name for path in core.AGENTS.glob("skills/*/SKILL.md")
            )
            duplicate = pi_home / "skills" / canonical_name
            duplicate.mkdir(parents=True)
            (duplicate / "SKILL.md").write_text("stale duplicate\n")
            (pi_home / "settings.json").write_text(json.dumps({"externalSetting": True}))
            (pi_home / "models.json").write_text(
                json.dumps({"providers": {"external-provider": {"models": []}}})
            )
            (pi_home / "presets.json").write_text(json.dumps({"external-preset": {}}))
            (pi_home / "extensions/external.ts").write_text("export default () => {};\n")

            sync.sync_pi(home, deploy_skills=True, deploy_plugins=False)

            settings = json.loads((pi_home / "settings.json").read_text())
            models = json.loads((pi_home / "models.json").read_text())
            presets = json.loads((pi_home / "presets.json").read_text())
            self.assertTrue(settings["externalSetting"])
            self.assertIn("external-provider", models["providers"])
            self.assertIn("external-preset", presets)
            self.assertTrue((pi_home / "extensions/external.ts").exists())
            self.assertTrue((pi_home / "skills/external-skill/SKILL.md").exists())
            self.assertFalse((pi_home / "skills" / canonical_name).exists())
            self.assertTrue((home / ".agents/skills" / canonical_name / "SKILL.md").exists())
            self.assertFalse((pi_home / "settings.json").is_symlink())
            self.assertEqual((pi_home / "sessions").stat().st_mode & 0o777, 0o700)
            self.assertEqual(session.stat().st_mode & 0o777, 0o600)
            self.assertEqual(drift_mod.drift(home, ("pi",), verify_plugins=False), 0)

            (pi_home / "extensions/welcome.ts").write_text("drift\n")
            settings.pop("defaultPreset")
            (pi_home / "settings.json").write_text(json.dumps(settings))

            self.assertEqual(drift_mod.drift(home, ("pi",), verify_plugins=False), 1)

    @patch.object(drift_mod.shutil, "which", return_value=None)
    def test_pi_drift_requires_cli(self, _which) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            sync.sync_pi(home, deploy_skills=True, deploy_plugins=False)

            self.assertEqual(drift_mod.drift(home, ("pi",), verify_plugins=False), 1)

    def test_codex_sync_deploys_and_checks_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)

            sync.sync_codex(home, deploy_skills=False, deploy_plugins=False)
            self.deploy_skills(home, ".agents/skills")

            quick = home / ".codex/quick.config.toml"
            deep = home / ".codex/deep.config.toml"
            self.assertEqual(tomllib.loads(quick.read_text())["model_reasoning_effort"], "low")
            self.assertEqual(tomllib.loads(deep.read_text())["model_reasoning_effort"], "high")
            self.assertEqual(tomllib.loads(quick.read_text())["approval_policy"], "on-request")
            self.assertEqual(drift_mod.drift(home, ("codex",), verify_plugins=False), 0)

            quick.write_text('model_reasoning_effort = "medium"\n')

            self.assertEqual(drift_mod.drift(home, ("codex",), verify_plugins=False), 1)

    def test_codex_rule_merge_preserves_safe_additions_and_drops_bypasses(self) -> None:
        canonical = 'prefix_rule(pattern=["git", "status"], decision="allow")\n'
        live = (
            canonical
            + "\n# --- Locally approved additions ---\n"
            + "\n".join(
                [
                    'prefix_rule(pattern=["gh", "pr", "view"], decision="allow")',
                    'prefix_rule(pattern=["git", "commit", "--no-verify"], decision="allow")',
                    'prefix_rule(pattern=["rm", "-rf"], decision="allow")',
                ]
            )
        )

        merged = codex.merge_codex_rules(canonical, live)

        self.assertIn('["gh", "pr", "view"]', merged)
        self.assertNotIn("--no-verify", merged)
        self.assertNotIn('["rm", "-rf"]', merged)

    def test_codex_rule_merge_preserves_approvals_outside_marker_section(self) -> None:
        canonical = 'prefix_rule(pattern=["git", "status"], decision="allow")\n'
        approval = 'prefix_rule(pattern=["cargo", "check"], decision="allow")'
        live = f"{approval}\n{canonical}{approval}\n"

        merged = codex.merge_codex_rules(canonical, live)

        self.assertIn("# --- Locally approved additions ---", merged)
        self.assertEqual(merged.count(approval), 1)
        self.assertLess(merged.index(canonical.strip()), merged.index(approval))

    def test_codex_merge_preserves_other_sections_and_external_mcp(self) -> None:
        source = """\
model = "example"

[mcp_servers.external]
command = "tool"

[mcp_servers.context7]
command = "retired"

[tui]
theme = "old"
other = true
"""

        merged = codex.merge_codex_config(source)
        parsed = tomllib.loads(merged)

        self.assertEqual(parsed["model"], "example")
        self.assertEqual(parsed["sandbox_mode"], "workspace-write")
        self.assertEqual(parsed["approval_policy"], "on-request")
        self.assertIn("external", parsed["mcp_servers"])
        self.assertNotIn("context7", parsed["mcp_servers"])
        self.assertEqual(parsed["tui"]["theme"], "Sublime Snazzy")
        self.assertEqual(parsed["tui"]["terminal_title"], ["spinner", "project"])
        self.assertTrue(parsed["tui"]["other"])

    def test_codex_merge_preserves_explicit_safety_policy(self) -> None:
        merged = codex.merge_codex_config(
            'sandbox_mode = "read-only"\napproval_policy = "untrusted"\n'
        )
        parsed = tomllib.loads(merged)

        self.assertEqual(parsed["sandbox_mode"], "read-only")
        self.assertEqual(parsed["approval_policy"], "untrusted")

    def test_codex_merge_replaces_nested_tui_and_preserves_nested_mcp(self) -> None:
        source = """\
model = "example"

[tui]
theme = "old"

[tui.model_availability_nux]
"gpt-5.5" = 4

[mcp_servers.external]
command = "tool"

[mcp_servers.external.env]
TOKEN = "preserved"

[features]
js_repl = false
"""

        parsed = tomllib.loads(codex.merge_codex_config(source))

        self.assertEqual(parsed["tui"]["theme"], "Sublime Snazzy")
        self.assertEqual(parsed["tui"]["model_availability_nux"], {"gpt-5.5": 4})
        self.assertEqual(parsed["mcp_servers"]["external"]["env"]["TOKEN"], "preserved")
        self.assertFalse(parsed["features"]["js_repl"])

    def test_codex_merge_rejects_malformed_toml(self) -> None:
        with self.assertRaises(core.WorkbenchError):
            codex.merge_codex_config("[")

    def test_codex_merge_is_idempotent(self) -> None:
        fixtures = [
            "",
            'model = "example"\n\n[mcp_servers.external]\ncommand = "tool"\n',
            'sandbox_mode = "read-only"\napproval_policy = "untrusted"\n',
            "[tui]\ntheme = \"old\"\n\n[tui.model_availability_nux]\n'gpt-5.5' = 4\n",
        ]
        for source in fixtures:
            with self.subTest(source=source):
                once = codex.merge_codex_config(source)

                self.assertEqual(codex.merge_codex_config(once), once)

    def test_drop_tables_is_line_based_but_guard_rejects_corruption(self) -> None:
        # Documents the known ceiling: _drop_tables cannot tell a real [tui]
        # header from one inside a multi-line string, so it truncates the
        # string mid-value. The round-trip guard turns that corruption into
        # a WorkbenchError instead of writing broken TOML.
        adversarial = 'description = """\n[tui]\ntheme = "fake"\n"""\n'

        truncated = codex._drop_tables(adversarial, ("[tui",))

        self.assertEqual(truncated, 'description = """')
        with self.assertRaises(core.WorkbenchError):
            codex.merge_codex_config(adversarial)

    def test_toml_value_rejects_unsupported_scalar_types(self) -> None:
        self.assertEqual(codex._toml_value(4), "4")
        with self.assertRaises(core.WorkbenchError):
            codex._toml_value(None)

    def test_check_reports_codex_drift_for_tombstoned_mcp(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            sync.sync_codex(home, deploy_skills=False, deploy_plugins=False)
            self.deploy_skills(home, ".agents/skills")
            config = home / ".codex/config.toml"
            config.write_text(
                config.read_text() + '\n[mcp_servers.context7]\ncommand = "retired"\n'
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = drift_mod.drift(home, ("codex",), verify_plugins=False)

            self.assertEqual(exit_code, 1)
            self.assertIn(
                "DRIFT retired codex MCP still present: context7",
                output.getvalue(),
            )

    def test_check_subagents_flags_retired_leftovers_as_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw)
            (destination / "docs-scribe.toml").write_text('name = "docs-scribe"\n')
            findings: list[str] = []
            external: list[str] = []

            drift_mod._check_subagents("codex", destination, findings, external)

            self.assertIn("DRIFT retired codex subagent still present: docs-scribe", findings)
            self.assertNotIn("EXTERNAL codex subagent: docs-scribe", external)

    def test_codex_subagents_render_read_only_sandbox_for_non_writing_tools(
        self,
    ) -> None:
        template = "---\nname: example\ndescription: Example subagent.\n{tools}---\n\nBody.\n"
        with tempfile.TemporaryDirectory() as raw:
            restricted_path = Path(raw) / "restricted.md"
            restricted_path.write_text(template.format(tools="tools: Read, Grep, Glob, Bash\n"))
            writer_path = Path(raw) / "writer.md"
            writer_path.write_text(template.format(tools="tools: Read, Edit\n"))
            unrestricted_path = Path(raw) / "unrestricted.md"
            unrestricted_path.write_text(template.format(tools=""))

            restricted = tomllib.loads(codex._render_codex_subagent(restricted_path))
            writer = tomllib.loads(codex._render_codex_subagent(writer_path))
            unrestricted = tomllib.loads(codex._render_codex_subagent(unrestricted_path))

        self.assertEqual(restricted["sandbox_mode"], "read-only")
        self.assertNotIn("sandbox_mode", writer)
        self.assertNotIn("sandbox_mode", unrestricted)

    def test_destructive_guard_allows_benign_command(self) -> None:
        result = self.run_hook(
            "guard-destructive-shell.sh", {"tool_input": {"command": "git status"}}
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_destructive_guard_blocks_any_recursive_force_delete(self) -> None:
        result = self.run_hook(
            "guard-destructive-shell.sh", {"tool_input": {"command": "rm -rf build"}}
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("recursive force-delete", result.stderr)

    def test_destructive_guard_blocks_disk_destroy(self) -> None:
        result = self.run_hook(
            "guard-destructive-shell.sh",
            {"tool_input": {"command": "diskutil eraseDisk APFS Blank disk4"}},
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("disk", result.stderr)

    def test_destructive_guard_blocks_hook_bypass(self) -> None:
        result = self.run_hook(
            "guard-destructive-shell.sh",
            {"tool_input": {"command": "git commit --no-verify -m unsafe"}},
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("--no-verify", result.stderr)

    def test_destructive_guard_blocks_alias_escape_and_eval(self) -> None:
        for command in (r"\rm -rf build", 'x="rm -rf build"; eval $x'):
            with self.subTest(command=command):
                result = self.run_hook(
                    "guard-destructive-shell.sh",
                    {"tool_input": {"command": command}},
                )

                self.assertEqual(result.returncode, 2, result.stderr)

    def test_sensitive_guard_blocks_secret_files_case_insensitively(self) -> None:
        for path in (".env", ".ENV", "conf/secrets.JSON", "id_ed25519", "api.KEY"):
            with self.subTest(path=path):
                result = self.run_hook(
                    "guard-sensitive-file.sh",
                    {"tool_input": {"file_path": path}},
                )

                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("sensitive file", result.stderr)

    def test_sensitive_guard_allows_templates_and_ordinary_files(self) -> None:
        for path in (".env.example", "keys.pub", "src/main.py"):
            with self.subTest(path=path):
                result = self.run_hook(
                    "guard-sensitive-file.sh",
                    {"tool_input": {"file_path": path}},
                )

                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
