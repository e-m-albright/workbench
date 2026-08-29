import { describe, expect, mock, test } from "bun:test";

mock.module("@earendil-works/pi-coding-agent", () => ({ getAgentDir: () => "/tmp/pi-agent" }));
const {
	default: inferenceRouter,
	classifyHardRule,
	formatRouteLabel,
	isSensitiveToolCall,
	parseClassifierDecision,
} = await import("../agents/pi/extensions/inference-router");
import type { RouterConfig } from "../agents/pi/extensions/inference-router";

const theme = {
	fg: (_color: string, text: string) => text,
};

const config: RouterConfig = {
	defaultMode: "frontier",
	frontier: { provider: "openai-codex", model: "gpt-5.6-sol" },
	private: { provider: "omlx", model: "Qwen3.6-35B-A3B-oQ4e-mtp" },
	classifier: {
		baseUrl: "http://localhost:8000/v1",
		model: "Qwen3.6-35B-A3B-oQ4e-mtp",
		timeoutMs: 1500,
	},
	privatePathFragments: ["/code/private/"],
};

describe("Pi inference router policy", () => {
	test("keeps private workspaces local without asking a classifier", () => {
		expect(classifyHardRule("Refactor this module", "/home/dev/code/private/project", config)).toEqual({
			route: "private",
			reason: "private_workspace",
		});
	});

	test("recognizes explicit personal-data requests", () => {
		expect(classifyHardRule("Show me my task queue for today", "/home/dev", config)).toEqual({
			route: "private",
			reason: "personal_data",
		});
	});

	test("leaves ordinary ambiguous input to the local classifier", () => {
		expect(
			classifyHardRule("Explain this tradeoff", "/home/dev/code/public/project", config),
		).toBeUndefined();
	});

	test("accepts only the small categorical classifier contract", () => {
		expect(parseClassifierDecision('{"route":"private","reason":"simple"}')).toEqual({
			route: "private",
			reason: "simple",
		});
		expect(parseClassifierDecision('{"route":"frontier","reason":"coding"}')).toEqual({
			route: "frontier",
			reason: "coding",
		});
		expect(parseClassifierDecision('{"route":"frontier","reason":"invented"}')).toBeUndefined();
		expect(parseClassifierDecision("frontier")).toBeUndefined();
	});

	test("formats fixed routes without repeating the mode and selected target", () => {
		expect(formatRouteLabel("frontier", { route: "frontier", reason: "coding" })).toBe("frontier");
		expect(formatRouteLabel("private", { route: "private", reason: "personal_data" })).toBe("private");
	});

	test("keeps the selected target and reason visible in auto mode", () => {
		expect(formatRouteLabel("auto")).toBe("auto");
		expect(formatRouteLabel("auto", { route: "frontier", reason: "coding" })).toBe(
			"auto → frontier (coding)",
		);
	});

	test("keeps plain Pi on the configured frontier default even in a private workspace", async () => {
		const handlers = new Map<string, (...args: any[]) => any>();
		const selected: unknown[] = [];
		const frontierModel = { provider: "openai-codex", id: "gpt-5.6-sol" };
		const pi = {
			registerFlag: () => undefined,
			registerCommand: () => undefined,
			on: (event: string, handler: (...args: any[]) => any) => handlers.set(event, handler),
			getFlag: () => undefined,
			setModel: async (model: unknown) => {
				selected.push(model);
				return true;
			},
		} as any;
		const ctx = {
			cwd: "/home/dev/code/private/project",
			modelRegistry: { find: () => frontierModel },
			ui: { theme, setStatus: () => undefined, notify: () => undefined },
		} as any;

		inferenceRouter(pi);
		await handlers.get("session_start")?.({}, ctx);

		expect(selected).toEqual([frontierModel]);
	});

	test("blocks an explicit private route when the local model is unavailable", async () => {
		const handlers = new Map<string, (...args: any[]) => any>();
		const editorValues: string[] = [];
		const notifications: string[] = [];
		const pi = {
			registerFlag: () => undefined,
			registerCommand: () => undefined,
			on: (event: string, handler: (...args: any[]) => any) => handlers.set(event, handler),
			getFlag: () => "private",
			setModel: async () => false,
		} as any;
		const ctx = {
			cwd: "/home/dev/code/private/project",
			modelRegistry: { find: () => undefined },
			ui: {
				theme,
				setStatus: () => undefined,
				notify: (message: string) => notifications.push(message),
				setEditorText: (value: string) => editorValues.push(value),
			},
		} as any;

		inferenceRouter(pi);
		await handlers.get("session_start")?.({}, ctx);
		const result = await handlers.get("input")?.({ source: "user", text: "Private prompt" }, ctx);

		expect(result).toEqual({ action: "handled" });
		expect(editorValues).toEqual(["Private prompt"]);
		expect(notifications).toContain("Private route blocked: the local model is unavailable");
	});

	test("treats connector and private-path tool calls as sensitive", () => {
		expect(isSensitiveToolCall("gmail_get_thread", {} as never, config)).toBe(true);
		expect(isSensitiveToolCall("apple_notes_get", {} as never, config)).toBe(true);
		expect(
			isSensitiveToolCall("read", { path: "/home/dev/code/private/project/file.md" } as never, config),
		).toBe(true);
		expect(isSensitiveToolCall("bash", { command: "notes actions work" } as never, config)).toBe(true);
		expect(
			isSensitiveToolCall("read", { path: "/home/dev/code/public/project/file.md" } as never, config),
		).toBe(false);
	});
});
