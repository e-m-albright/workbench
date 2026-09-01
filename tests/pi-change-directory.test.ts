import { expect, test } from "bun:test";
import { mkdtempSync, mkdirSync, realpathSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const forkCalls: Array<[string, string]> = [];
const sessions = {
	forkFrom: (source: string, target: string) => {
		forkCalls.push([source, target]);
		return { getSessionFile: () => "/tmp/target-session.jsonl" };
	},
};

const {
	default: changeDirectoryExtension,
	resolveDirectory,
	splitZoxideQuery,
} = await import("../agents/pi/extensions/change-directory");

test("resolves relative and quoted explicit directories", () => {
	const root = mkdtempSync(join(tmpdir(), "pi-cd-"));
	const target = join(root, "folder with spaces");
	mkdirSync(target);

	expect(resolveDirectory('"folder with spaces"', root)).toBe(realpathSync(target));
	expect(splitZoxideQuery(" private   notes ")).toEqual(["private", "notes"]);
});

test("zoxide jumps by forking the conversation into the matched project", async () => {
	forkCalls.length = 0;
	const root = mkdtempSync(join(tmpdir(), "pi-z-"));
	const sourceCwd = join(root, "source");
	const targetCwd = join(root, "target");
	mkdirSync(sourceCwd);
	mkdirSync(targetCwd);

	const resolvedTarget = realpathSync(targetCwd);
	const commands = new Map<string, any>();
	const execCalls: Array<[string, string[]]> = [];
	const pi = {
		registerCommand: (name: string, command: any) => commands.set(name, command),
		exec: async (command: string, args: string[]) => {
			execCalls.push([command, args]);
			return { code: 0, stdout: `${targetCwd}\n`, stderr: "" };
		},
	};
	changeDirectoryExtension(pi as any, sessions as any);

	let switchedTo: string | undefined;
	let replacementNotice: string | undefined;
	const ctx = {
		cwd: sourceCwd,
		waitForIdle: async () => {},
		sessionManager: { getSessionFile: () => "/tmp/source-session.jsonl" },
		switchSession: async (path: string, options: any) => {
			switchedTo = path;
			await options.withSession({
				cwd: resolvedTarget,
				ui: { notify: (message: string) => (replacementNotice = message) },
			});
			return { cancelled: false };
		},
		ui: { notify: () => {}, input: async () => undefined },
	};

	await commands.get("z").handler("target", ctx);

	expect(execCalls).toEqual([["zoxide", ["query", "--exclude", sourceCwd, "target"]]]);
	expect(forkCalls).toEqual([["/tmp/source-session.jsonl", resolvedTarget]]);
	expect(switchedTo).toBe("/tmp/target-session.jsonl");
	expect(replacementNotice).toBe(`Working directory: ${resolvedTarget}`);
});
