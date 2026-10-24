import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { describe, expect, test, vi } from "vitest";

vi.doMock("@earendil-works/pi-coding-agent", () => ({}));
const { classifyCommand, default: safeGit } = await import("../agents/pi/extensions/safe-git");

test("safe-git status reports one effective configuration and labels session overrides", async () => {
	const agent = mkdtempSync(resolve(tmpdir(), "pi-status-"));
	writeFileSync(resolve(agent, "settings.json"), JSON.stringify({ safeGit: { promptLevel: "medium" } }));
	vi.stubEnv("PI_CODING_AGENT_DIR", agent);
	try {
		const commands = new Map<string, { handler: (...args: any[]) => Promise<void> }>();
		const notify = vi.fn();
		safeGit({ on() {}, registerCommand: (name: string, command: any) => commands.set(name, command) } as any);
		const ctx = { cwd: agent, isProjectTrusted: () => false, ui: { notify } };
		await commands.get("safegit-status")?.handler("", ctx);
		const status = notify.mock.lastCall?.[0] as string;
		expect(status).toContain("Prompt Level: medium");
		expect(status.match(/Prompt Level:/g)).toHaveLength(1);
		expect(status).not.toContain("session override");
		await commands.get("safegit-level")?.handler("none", ctx);
		await commands.get("safegit")?.handler("", ctx);
		await commands.get("safegit-status")?.handler("", ctx);
		expect(notify.mock.lastCall?.[0]).toContain("Prompt Level: none (session override)");
		expect(notify.mock.lastCall?.[0]).toContain("Enabled: 🔓 OFF (session override)");
	} finally {
		vi.unstubAllEnvs();
		rmSync(agent, { recursive: true, force: true });
	}
});

test("safe-git reads configured protection and only trusts approved project overrides", async () => {
	const root = mkdtempSync(resolve(tmpdir(), "pi-settings-"));
	const agent = resolve(root, "agent");
	const cwd = resolve(root, "project");
	mkdirSync(agent);
	mkdirSync(resolve(cwd, ".pi"), { recursive: true });
	writeFileSync(resolve(agent, "settings.json"), JSON.stringify({ safeGit: { promptLevel: "medium" } }));
	writeFileSync(resolve(cwd, ".pi/settings.json"), JSON.stringify({ safeGit: { enabledByDefault: false } }));
	vi.stubEnv("PI_CODING_AGENT_DIR", agent);
	try {
		const handlers = new Map<string, (...args: any[]) => any>();
		safeGit({ on: (name: string, fn: any) => handlers.set(name, fn), registerCommand() {} } as any);
		const ctx = { cwd, hasUI: false, isProjectTrusted: () => false };
		const event = { toolName: "bash", input: { command: "git push origin main" } };
		expect(await handlers.get("tool_call")?.(event, ctx)).toMatchObject({ block: true });
		ctx.isProjectTrusted = () => true;
		expect(await handlers.get("tool_call")?.(event, ctx)).toBeUndefined();
		writeFileSync(
			resolve(cwd, ".pi/settings.json"),
			JSON.stringify({ safeGit: { enabledByDefault: "false", promptLevel: "invalid" } }),
		);
		expect(
			await handlers.get("tool_call")?.({ toolName: "bash", input: { command: "git reset --hard" } }, ctx),
		).toMatchObject({ block: true });
	} finally {
		vi.unstubAllEnvs();
		rmSync(root, { recursive: true, force: true });
	}
});

test("default protection blocks short force pushes without prompting for ordinary pushes", async () => {
	const agent = mkdtempSync(resolve(tmpdir(), "pi-force-push-"));
	vi.stubEnv("PI_CODING_AGENT_DIR", agent);
	try {
		const handlers = new Map<string, (...args: any[]) => any>();
		safeGit({ on: (name: string, fn: any) => handlers.set(name, fn), registerCommand() {} } as any);
		const ctx = { cwd: agent, hasUI: false, isProjectTrusted: () => false };
		for (const command of ["git push -f origin main", "git push -vf origin main"]) {
			expect(await handlers.get("tool_call")?.({ toolName: "bash", input: { command } }, ctx)).toMatchObject({
				block: true,
			});
		}
		expect(
			await handlers.get("tool_call")?.(
				{ toolName: "bash", input: { command: "git push origin main" } },
				ctx,
			),
		).toBeUndefined();
	} finally {
		vi.unstubAllEnvs();
		rmSync(agent, { recursive: true, force: true });
	}
});

interface Vector {
	command: string;
	hook: "block" | "allow";
	safeGit: "high" | "medium" | null;
}

const vectors: Vector[] = JSON.parse(
	readFileSync(resolve(import.meta.dirname, "data/git-guard-vectors.json"), "utf8"),
).vectors;

describe("safe-git command classification", () => {
	test("shared guard vectors classify at the expected severity", () => {
		for (const { command, safeGit } of vectors) {
			const match = classifyCommand(command);
			if (safeGit === null) {
				expect(match, command).toBeNull();
			} else {
				expect(match, command).not.toBeNull();
				expect(match?.severity, command).toBe(safeGit);
			}
		}
	});

	test("first match wins: a force push classifies as force push, not plain push", () => {
		expect(classifyCommand("git push --force origin main")?.action).toBe("force push");
		expect(classifyCommand("git push origin +main")?.action).toBe("force push");
		expect(classifyCommand("git push origin main")?.action).toBe("push");
	});

	test("retains destructive commands embedded in Git option values", () => {
		expect(classifyCommand("git -c 'alias.wipe=!git reset --hard' wipe")?.severity).toBe("high");
	});

	test("ordinary merged-branch cleanup is not a high-risk operation", () => {
		expect(classifyCommand("git branch -d shipped-feature")?.severity).toBe("medium");
		expect(classifyCommand("git -C checkout branch -d shipped-feature")?.severity).toBe("medium");
		expect(classifyCommand("git branch -D unmerged-feature")?.severity).toBe("high");
		expect(classifyCommand("git stash pop stash@{0}")).toBeNull();
		expect(classifyCommand("git stash drop stash@{0}")?.severity).toBe("high");
	});

	test("gh reads pass silently so session approvals never cover unseen mutations", () => {
		expect(classifyCommand("gh pr view 12")).toBeNull();
		expect(classifyCommand("gh run list")).toBeNull();
		expect(classifyCommand("gh pr merge 12")?.action).toBe("mutating GitHub CLI");
	});
});
