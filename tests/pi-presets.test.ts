import { describe, expect, mock, test } from "bun:test";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";

mock.module("@earendil-works/pi-coding-agent", () => ({ getAgentDir: () => "/tmp/pi-agent" }));
const {
	default: presetsExtension,
	isConnectorTool,
	presetCanAct,
} = await import("../agents/pi/extensions/presets");

describe("Pi preset taint guard", () => {
	test("classifies connector tools as untrusted-content sources", () => {
		for (const tool of ["gmail_search_threads", "calendar_list_events", "strava_get_activity"]) {
			expect(isConnectorTool(tool)).toBe(true);
		}
		for (const tool of ["read", "bash", "grep", "edit"]) {
			expect(isConnectorTool(tool)).toBe(false);
		}
	});

	test("identifies acting presets by shell/edit/write tools", () => {
		expect(presetCanAct({ tools: ["read", "grep", "bash"] })).toBe(true);
		expect(presetCanAct({ tools: ["read", "grep", "edit", "write"] })).toBe(true);
		expect(presetCanAct({ tools: ["workspace_files"] })).toBe(true);
		expect(presetCanAct({ tools: ["read", "grep", "gmail_search_threads"] })).toBe(false);
		expect(presetCanAct({})).toBe(false);
	});

	test("lets dev sessions manage one bounded worker autonomously", () => {
		const path = resolve(import.meta.dir, "../agents/pi/presets.json");
		const presets = JSON.parse(readFileSync(path, "utf8")) as {
			dev: { tools: string[]; instructions: string };
		};
		expect(presets.dev.tools).toContain("workspace_files");
		expect(Object.keys(presets)).toEqual(["dev"]);
		expect(presets.dev.tools).toContain("worker");
		expect(presets.dev.tools).toContain("ingress_discard");
		expect(presets.dev.instructions).toContain("Autonomously call the worker tool");
		expect(presets.dev.instructions).toContain("no user approval is required");
		expect(presets.dev.instructions).toContain("Do not delegate small tasks");
	});

	test("uses Pi's native fullscreen transcript instead of a custom reader", () => {
		const path = resolve(import.meta.dir, "../agents/pi/settings.json");
		const settings = JSON.parse(readFileSync(path, "utf8")) as { tuiMode?: string };
		expect(settings.tuiMode).toBe("fullscreen");
	});

	test("activates the configured default preset without an undocumented settings manager", async () => {
		const root = mkdtempSync(resolve(tmpdir(), "pi-presets-"));
		const agentDir = resolve(root, "agent");
		const cwd = resolve(root, "project");
		mkdirSync(agentDir, { recursive: true });
		mkdirSync(cwd, { recursive: true });
		writeFileSync(resolve(agentDir, "settings.json"), JSON.stringify({ defaultPreset: "dev" }));
		writeFileSync(
			resolve(agentDir, "presets.json"),
			JSON.stringify({ dev: { tools: ["read", "bash", "edit", "write"] } }),
		);

		const originalAgentDir = process.env.PI_CODING_AGENT_DIR;
		process.env.PI_CODING_AGENT_DIR = agentDir;
		try {
			const handlers = new Map<string, (...args: any[]) => any>();
			let activeTools: string[] = [];
			const pi = {
				on: (event: string, handler: (...args: any[]) => any) => handlers.set(event, handler),
				registerFlag: () => {},
				registerCommand: () => {},
				getFlag: () => undefined,
				getAllTools: () => ["read", "bash", "edit", "write"].map((name) => ({ name })),
				setActiveTools: (tools: string[]) => {
					activeTools = tools;
				},
				setThinkingLevel: () => {},
			} as any;
			presetsExtension(pi);

			await handlers.get("session_start")?.(
				{},
				{
					cwd,
					ui: { notify: () => {} },
				},
			);

			expect(activeTools).toEqual(["read", "bash", "edit", "write"]);
		} finally {
			if (originalAgentDir === undefined) delete process.env.PI_CODING_AGENT_DIR;
			else process.env.PI_CODING_AGENT_DIR = originalAgentDir;
		}
	});
});
