import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { afterEach, describe, expect, test, vi } from "vitest";

const parseArgs = vi.fn(() => ({}));
vi.doMock("@earendil-works/pi-coding-agent", () => ({ getAgentDir: () => "/tmp/pi-agent", parseArgs }));
const {
	default: presetsExtension,
	isConnectorTool,
	presetCanAct,
} = await import("../agents/pi/extensions/presets");

const temporaryHomes: string[] = [];
afterEach(() => {
	vi.unstubAllEnvs();
	for (const path of temporaryHomes.splice(0)) rmSync(path, { recursive: true, force: true });
});

function policyPresetHarness(provider: string) {
	const agent = mkdtempSync(resolve(tmpdir(), "pi-preset-policy-"));
	temporaryHomes.push(agent);
	vi.stubEnv("PI_CODING_AGENT_DIR", agent);
	vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", undefined);
	vi.stubEnv("WORKBENCH_PI_MODE", undefined);
	writeFileSync(resolve(agent, "settings.json"), JSON.stringify({ defaultPreset: "dev" }));
	writeFileSync(
		resolve(agent, "presets.json"),
		JSON.stringify({ dev: { tools: ["read", "bash", "strava_get_activity", "blocked_tool"] } }),
	);
	writeFileSync(
		resolve(agent, "permission-policy.json"),
		JSON.stringify({
			privateProviders: ["omlx"],
			privateOnlyTools: ["strava_get_activity"],
			blockedTools: ["blocked_tool"],
		}),
	);
	const handlers = new Map<string, (...args: any[]) => any>();
	let tools: string[] = [];
	const pi = {
		registerFlag() {},
		registerCommand() {},
		getFlag() {},
		on: (name: string, handler: any) => handlers.set(name, handler),
		getAllTools: () =>
			["read", "bash", "custom", "strava_get_activity", "blocked_tool"].map((name) => ({ name })),
		getActiveTools: () => [...tools],
		setActiveTools: (value: string[]) => {
			tools = [...value];
		},
	};
	presetsExtension(pi as any);
	return { pi, handlers, ctx: { cwd: agent, model: { provider }, ui: { notify() {} } } };
}

test("hosted presets advertise only tools eligible under the installed policy", async () => {
	const { pi, handlers, ctx } = policyPresetHarness("openai-codex");
	await handlers.get("session_start")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["read", "bash"]);
});

test("private presets retain private-only tools while hiding universally blocked tools", async () => {
	const { pi, handlers, ctx } = policyPresetHarness("omlx");
	await handlers.get("session_start")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["read", "bash", "strava_get_activity"]);
});

test("managed sessions hide private-only tools even when a local provider is selected", async () => {
	const { pi, handlers, ctx } = policyPresetHarness("omlx");
	vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "managed");
	await handlers.get("session_start")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["read", "bash"]);
});

test("a fully filtered preset restores eligible tools when the provider changes", async () => {
	const { pi, handlers, ctx } = policyPresetHarness("openai-codex");
	writeFileSync(
		resolve(ctx.cwd, "presets.json"),
		JSON.stringify({ dev: { tools: ["strava_get_activity"] } }),
	);
	await handlers.get("session_start")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual([]);
	ctx.model.provider = "omlx";
	await handlers.get("model_select")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["strava_get_activity"]);
});

test("provider changes restore and hide policy-filtered tools without reapplying the preset", async () => {
	const { pi, handlers, ctx } = policyPresetHarness("openai-codex");
	await handlers.get("session_start")?.({}, ctx);
	ctx.model.provider = "omlx";
	await handlers.get("model_select")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["read", "bash", "strava_get_activity"]);
	ctx.model.provider = "openai-codex";
	await handlers.get("model_select")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["read", "bash"]);
});

test("provider changes preserve deliberate additions and removals from the tool selection", async () => {
	const { pi, handlers, ctx } = policyPresetHarness("omlx");
	await handlers.get("session_start")?.({}, ctx);
	pi.setActiveTools(["read", "custom"]);
	ctx.model.provider = "openai-codex";
	await handlers.get("model_select")?.({}, ctx);
	ctx.model.provider = "omlx";
	await handlers.get("model_select")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["read", "custom"]);
});

test("provider filtering changes only restricted tools in a custom selection", async () => {
	const { pi, handlers, ctx } = policyPresetHarness("omlx");
	await handlers.get("session_start")?.({}, ctx);
	pi.setActiveTools(["read", "custom", "strava_get_activity"]);
	ctx.model.provider = "openai-codex";
	await handlers.get("model_select")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["read", "custom"]);
	ctx.model.provider = "omlx";
	await handlers.get("model_select")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["read", "custom", "strava_get_activity"]);
});

test("a manual hosted tool selection supersedes tools hidden by the preset", async () => {
	const { pi, handlers, ctx } = policyPresetHarness("openai-codex");
	await handlers.get("session_start")?.({}, ctx);
	pi.setActiveTools(["read", "custom"]);
	ctx.model.provider = "omlx";
	await handlers.get("model_select")?.({}, ctx);
	expect(pi.getActiveTools()).toEqual(["read", "custom"]);
});

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
		const path = resolve(import.meta.dirname, "../agents/pi/presets.json");
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
		const path = resolve(import.meta.dirname, "../agents/pi/settings.json");
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
		mkdirSync(resolve(cwd, ".pi"));
		writeFileSync(resolve(cwd, ".pi/settings.json"), JSON.stringify({ defaultPreset: "unsafe" }));
		writeFileSync(
			resolve(cwd, ".pi/presets.json"),
			JSON.stringify({ unsafe: { tools: ["read"] }, dev: { tools: ["read"] } }),
		);
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
					isProjectTrusted: () => false,
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

test("the default preset preserves explicit native thinking flags", async () => {
	const agent = mkdtempSync(resolve(tmpdir(), "pi-thinking-"));
	writeFileSync(resolve(agent, "settings.json"), JSON.stringify({ defaultPreset: "dev" }));
	writeFileSync(resolve(agent, "presets.json"), JSON.stringify({ dev: { thinkingLevel: "medium" } }));
	const previous = process.env.PI_CODING_AGENT_DIR;
	process.env.PI_CODING_AGENT_DIR = agent;
	parseArgs.mockReturnValue({ thinking: "high" });
	try {
		const handlers = new Map<string, any>();
		const setThinkingLevel = vi.fn();
		presetsExtension({
			registerFlag() {},
			registerCommand() {},
			getFlag() {},
			on: (name: string, handler: any) => handlers.set(name, handler),
			setThinkingLevel,
		} as any);
		await handlers.get("session_start")({}, { cwd: agent, ui: { notify() {} } });
		expect(setThinkingLevel).not.toHaveBeenCalled();
	} finally {
		parseArgs.mockReturnValue({});
		if (previous === undefined) delete process.env.PI_CODING_AGENT_DIR;
		else process.env.PI_CODING_AGENT_DIR = previous;
	}
});
