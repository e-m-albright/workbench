from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).parents[1] / "scripts/workbench.py"
SPEC = importlib.util.spec_from_file_location("workbench_cli", MODULE_PATH)
assert SPEC and SPEC.loader
wb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wb)


class WorkbenchTests(unittest.TestCase):
    def run_hook(self, name: str, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(wb.AGENTS / "shared/hooks" / name)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_merge_mcp_preserves_external_and_removes_tombstones(self) -> None:
        merged = wb.merge_mcp(
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
        merged = wb.merge_mcp(
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

            with self.assertRaises(wb.WorkbenchError):
                wb.load_json(path, {})

            self.assertEqual(path.read_text(), "{")

    def test_write_text_keeps_one_backup(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "config.json"
            path.write_text("old")

            self.assertTrue(wb.write_text(path, "new"))

            self.assertEqual(path.read_text(), "new")
            self.assertEqual(path.with_name("config.json.bak").read_text(), "old")

    def test_launcher_resolves_global_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            link = Path(raw) / "workbench"
            link.symlink_to(wb.ROOT / "bin/workbench")

            result = subprocess.run(
                [str(link), "lint"], capture_output=True, text=True, check=False
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("OK 17 skills", result.stdout)

    def test_bare_launcher_renders_branded_complete_command_tree(self) -> None:
        result = subprocess.run(
            [str(wb.ROOT / "bin/workbench")],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("██╗    ██╗", result.stdout)
        self.assertIn("Usage: workbench [OPTIONS] COMMAND [ARGS]...", result.stdout)
        self.assertIn("Options", result.stdout)
        self.assertIn("Configuration — deploy and validate agent state", result.stdout)
        self.assertIn("sync [claude|codex|all]", result.stdout)
        self.assertIn("check [claude|codex|all]", result.stdout)
        self.assertIn("--no-skills", result.stdout)

    def test_banner_uses_ruby_truecolor_gradient_on_terminals(self) -> None:
        rendered = wb.gradient_banner(color=True)

        self.assertIn("\033[38;2;255;184;194m", rendered)
        self.assertIn("\033[38;2;101;0;24m", rendered)
        self.assertTrue(rendered.endswith("\033[0m"))

    def test_bare_just_uses_dotfiles_heading_convention(self) -> None:
        result = subprocess.run(
            ["just"], cwd=wb.ROOT, capture_output=True, text=True, check=False
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("workbench CLI", result.stdout)
        self.assertIn("dev tasks (cwd: repository root)", result.stdout)
        self.assertIn("[quality]", result.stdout)
        self.assertIn("[testing]", result.stdout)
        self.assertIn("[deployment]", result.stdout)

    def test_sync_help_explains_targets_and_optional_installers(self) -> None:
        result = subprocess.run(
            [str(wb.ROOT / "bin/workbench"), "sync", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("{claude,codex,all}", result.stdout)
        self.assertIn("--no-skills", result.stdout)
        self.assertIn("--no-plugins", result.stdout)

    @patch.object(wb.subprocess, "run")
    @patch.object(wb.shutil, "which", return_value="/usr/bin/npx")
    def test_skill_sync_removes_retired_skills_before_installing(
        self, _which, run
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            for name in wb.RETIRED_SKILLS:
                retired = home / ".agents/skills" / name
                retired.mkdir(parents=True)
                (retired / "SKILL.md").write_text("retired")

            wb._sync_skills("codex", home)

            for name in wb.RETIRED_SKILLS:
                self.assertFalse((home / ".agents/skills" / name).exists())

        remove_command = run.call_args_list[0].args[0]
        self.assertEqual(remove_command[:3], ["npx", "skills", "remove"])
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

            wb._check_skills(skill_root, "codex", findings, external)

            self.assertIn(
                "DRIFT retired codex skill still present: converge", findings
            )
            self.assertNotIn("EXTERNAL codex skill: converge", external)

    def test_skill_descriptions_fit_context_budget(self) -> None:
        descriptions = []
        for skill in wb.AGENTS.glob("skills/*/SKILL.md"):
            match = wb.re.search(
                r"^description:\s*([^\n]+)$", skill.read_text(), wb.re.MULTILINE
            )
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

            errors = wb._markdown_link_errors(root)

            self.assertEqual(len(errors), 1)
            self.assertIn("missing.md", errors[0])

    def test_repository_markdown_links_resolve(self) -> None:
        self.assertEqual(wb._markdown_link_errors(wb.ROOT), [])

    def test_sync_claude_preserves_unmanaged_settings(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            settings = home / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(
                json.dumps({"custom": 7, "permissions": {"custom": True}})
            )

            wb.sync_claude(home, deploy_skills=False)

            actual = json.loads(settings.read_text())
            self.assertEqual(actual["custom"], 7)
            self.assertTrue(actual["permissions"]["custom"])
            self.assertIn("enabledPlugins", actual)
            self.assertEqual(actual["defaultMode"], "auto")
            self.assertNotIn("defaultMode", actual["permissions"])
            self.assertTrue(actual["sandbox"]["enabled"])
            self.assertFalse(actual["sandbox"]["allowUnsandboxedCommands"])
            self.assertTrue((home / ".claude.json.bak").exists() is False)

    def test_plugin_inventory_parses_each_vendor_shape(self) -> None:
        claude = json.dumps([{"id": "example@market", "enabled": True}])
        codex = json.dumps(
            {"installed": [{"pluginId": "example@market", "enabled": True}]}
        )

        self.assertEqual(
            wb._installed_plugin_ids("claude", claude), {"example@market"}
        )
        self.assertEqual(
            wb._installed_plugin_ids("codex", codex), {"example@market"}
        )

    def test_codex_connector_plugins_are_declared(self) -> None:
        plugins = wb._string_array(wb.AGENTS / "codex/plugins.json")

        self.assertEqual(
            plugins,
            [
                "gmail@openai-curated",
                "google-calendar@openai-curated",
                "granola@openai-curated",
            ],
        )
        self.assertNotIn("granola", wb.active_mcp("codex"))

    def test_sync_removes_retired_workbench_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            hook_dir = home / wb.DATA_REL / "hooks"
            hook_dir.mkdir(parents=True)
            retired = hook_dir / "notify.sh"
            retired.write_text("#!/bin/sh\n")
            backup = hook_dir / "notify.sh.bak"
            backup.write_text("#!/bin/sh\n")

            wb.sync_claude(home, deploy_skills=False)

            self.assertFalse(retired.exists())
            self.assertFalse(backup.exists())
            self.assertTrue((hook_dir / "guard-destructive-shell.sh").exists())

    def test_codex_subagents_render_as_native_toml(self) -> None:
        source = wb.AGENTS / "subagents/code-reviewer.md"

        rendered = wb._render_codex_subagent(source)
        parsed = wb.tomllib.loads(rendered)

        self.assertEqual(parsed["name"], "code-reviewer")
        self.assertIn("correctness", parsed["description"])
        self.assertIn("review", parsed["developer_instructions"].lower())

    def test_sync_codex_replaces_markdown_subagents_and_prunes_retired(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / ".codex/agents"
            destination.mkdir(parents=True)
            (destination / "code-reviewer.md").write_text("stale")
            (destination / "docs-scribe.md").write_text("retired")

            wb._sync_subagents("codex", destination)

            self.assertFalse(list(destination.glob("*.md*")))
            self.assertFalse((destination / "docs-scribe.toml").exists())
            parsed = wb.tomllib.loads(
                (destination / "code-reviewer.toml").read_text()
            )
            self.assertEqual(parsed["name"], "code-reviewer")

    def test_check_detects_managed_file_content_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            wb.sync_claude(home, deploy_skills=False)
            skill_root = home / ".claude/skills"
            for source in wb.AGENTS.glob("skills/*"):
                if source.is_dir():
                    wb.shutil.copytree(source, skill_root / source.name)

            self.assertEqual(
                wb.check(home, ("claude",), verify_plugins=False), 0
            )

            (home / ".claude/hooks.json").write_text("{}\n")
            (home / ".claude/settings.json").write_text(
                json.dumps({"voiceEnabled": False})
            )

            self.assertEqual(
                wb.check(home, ("claude",), verify_plugins=False), 1
            )

    def test_temporary_home_sync_and_check_all_vendors(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            wb.sync_claude(home, deploy_skills=False, deploy_plugins=False)
            wb.sync_codex(home, deploy_skills=False, deploy_plugins=False)
            for root in (home / ".claude/skills", home / ".agents/skills"):
                for source in wb.AGENTS.glob("skills/*"):
                    if source.is_dir():
                        wb.shutil.copytree(source, root / source.name)

            self.assertEqual(
                wb.check(home, ("claude", "codex"), verify_plugins=False), 0
            )

    def test_codex_rule_merge_preserves_safe_additions_and_drops_bypasses(self) -> None:
        canonical = 'prefix_rule(pattern=["git", "status"], decision="allow")\n'
        live = canonical + "\n# --- Locally approved additions ---\n" + '\n'.join(
            [
                'prefix_rule(pattern=["gh", "pr", "view"], decision="allow")',
                'prefix_rule(pattern=["git", "commit", "--no-verify"], decision="allow")',
                'prefix_rule(pattern=["rm", "-rf"], decision="allow")',
            ]
        )

        merged = wb.merge_codex_rules(canonical, live)

        self.assertIn('["gh", "pr", "view"]', merged)
        self.assertNotIn("--no-verify", merged)
        self.assertNotIn('["rm", "-rf"]', merged)

    def test_codex_rule_merge_does_not_resurrect_removed_canonical_rules(self) -> None:
        removed = 'prefix_rule(pattern=["old", "tool"], decision="allow")'

        merged = wb.merge_codex_rules(
            'prefix_rule(pattern=["git", "status"], decision="allow")\n',
            removed + "\n",
        )

        self.assertNotIn(removed, merged)

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

        merged = wb.merge_codex_config(source)
        parsed = wb.tomllib.loads(merged)

        self.assertEqual(parsed["model"], "example")
        self.assertEqual(parsed["sandbox_mode"], "workspace-write")
        self.assertEqual(parsed["approval_policy"], "on-request")
        self.assertIn("external", parsed["mcp_servers"])
        self.assertNotIn("context7", parsed["mcp_servers"])
        self.assertEqual(parsed["tui"]["theme"], "Sublime Snazzy")
        self.assertTrue(parsed["tui"]["other"])

    def test_codex_merge_preserves_explicit_safety_policy(self) -> None:
        merged = wb.merge_codex_config(
            'sandbox_mode = "read-only"\napproval_policy = "untrusted"\n'
        )
        parsed = wb.tomllib.loads(merged)

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

        parsed = wb.tomllib.loads(wb.merge_codex_config(source))

        self.assertEqual(parsed["tui"]["theme"], "Sublime Snazzy")
        self.assertEqual(parsed["tui"]["model_availability_nux"], {"gpt-5.5": 4})
        self.assertEqual(parsed["mcp_servers"]["external"]["env"]["TOKEN"], "preserved")
        self.assertFalse(parsed["features"]["js_repl"])

    def test_codex_merge_rejects_malformed_toml(self) -> None:
        with self.assertRaises(wb.WorkbenchError):
            wb.merge_codex_config("[")

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


if __name__ == "__main__":
    unittest.main()
