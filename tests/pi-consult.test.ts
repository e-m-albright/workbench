import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, test, vi } from "vitest";
import consult from "../agents/pi/extensions/consult";

test("consult uses configured provider, model, and timeout without a settings manager", async () => {
	const root = mkdtempSync(join(tmpdir(), "pi-consult-"));
	const cwd = join(root, "project");
	mkdirSync(cwd);
	writeFileSync(
		join(root, "settings.json"),
		JSON.stringify({ consult: { provider: "codex", timeoutMs: 1234 } }),
	);
	vi.stubEnv("PI_CODING_AGENT_DIR", root);
	vi.stubEnv("WORKBENCH_PI_MODE", "hosted-unrestricted");
	vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "unrestricted");
	try {
		let command: any;
		const exec = vi.fn(async () => ({ code: 0, stdout: "ok" }));
		consult({ registerCommand: (_name: string, value: any) => (command = value), exec } as any);
		await command.handler("review", { cwd, isProjectTrusted: () => false, ui: { notify() {} } });
		expect(exec).toHaveBeenCalledWith("codex", expect.any(Array), expect.objectContaining({ timeout: 1234 }));
		writeFileSync(
			join(root, "settings.json"),
			JSON.stringify({ consult: { provider: "claude", model: "test-model", timeoutMs: "invalid" } }),
		);
		await command.handler("review", { cwd, isProjectTrusted: () => false, ui: { notify() {} } });
		expect(exec).toHaveBeenLastCalledWith(
			"claude",
			expect.arrayContaining(["--model", "test-model"]),
			expect.objectContaining({ timeout: 120000 }),
		);
	} finally {
		vi.unstubAllEnvs();
		rmSync(root, { recursive: true, force: true });
	}
});

test("restricted consult explains the missing cross-vendor grant without running a subprocess", async () => {
	vi.stubEnv("WORKBENCH_PI_MODE", "hosted-restricted");
	try {
		let command: any;
		const exec = vi.fn(async () => ({ code: 0, stdout: "ok" }));
		const notify = vi.fn();
		consult({ registerCommand: (_name: string, value: any) => (command = value), exec } as any);
		await command.handler("review", { cwd: "/tmp/example", ui: { notify } });
		expect(exec).not.toHaveBeenCalled();
		expect(notify).toHaveBeenCalledWith(expect.stringContaining("restricted"), "error");
	} finally {
		vi.unstubAllEnvs();
	}
});

test("local sessions cannot send a consult to cloud CLIs", async () => {
	const old = process.env.WORKBENCH_PI_MODE;
	process.env.WORKBENCH_PI_MODE = "local-unrestricted";
	try {
		let command: any;
		const calls: unknown[] = [];
		const notices: string[] = [];
		consult({
			registerCommand: (_name: string, value: any) => (command = value),
			exec: (...args: unknown[]) => {
				calls.push(args);
				return Promise.resolve({ code: 0, stdout: "ok" });
			},
		} as any);
		await command.handler("review private context", {
			cwd: "/tmp/example",
			model: { provider: "omlx" },
			ui: { notify: (text: string) => notices.push(text) },
		} as any);
		expect(calls).toEqual([]);
		expect(notices.join(" ")).toContain("local");
	} finally {
		if (old === undefined) delete process.env.WORKBENCH_PI_MODE;
		else process.env.WORKBENCH_PI_MODE = old;
	}
});
