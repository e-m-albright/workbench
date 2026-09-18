import { describe, expect, vi, test } from "vitest";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";

vi.doMock("@earendil-works/pi-coding-agent", () => ({ getAgentDir: () => "/tmp/pi-agent" }));
const { default: inferenceRouter } = await import("../agents/pi/extensions/inference-router");

import { tmpdir } from "node:os";
import { join } from "node:path";

const theme = { fg: (_color: string, text: string) => text };

describe("Pi model routing", () => {
	test("advertises the full context window exposed by oMLX", () => {
		const models = JSON.parse(readFileSync(new URL("../agents/pi/models.json", import.meta.url), "utf8"));
		const localModel = models.providers.omlx.models.find(
			(model: { id: string }) => model.id === "Qwen3.6-35B-A3B-oQ4e-mtp",
		);
		expect(localModel).toMatchObject({ contextWindow: 262144, maxTokens: 32768 });
	});

	test("defaults explicitly to frontier without automatic classification", () => {
		const router = JSON.parse(
			readFileSync(new URL("../agents/pi/inference-router.json", import.meta.url), "utf8"),
		);
		expect(router.defaultMode).toBe("frontier");
		expect(JSON.stringify(router)).not.toContain("classifier");
	});

	test("selects an explicit private route at session start", async () => {
		const handlers = new Map<string, (...args: any[]) => any>();
		const selected: unknown[] = [];
		const localModel = { provider: "omlx", id: "local" };
		const pi = {
			registerFlag: () => undefined,
			registerCommand: () => undefined,
			on: (event: string, handler: (...args: any[]) => any) => handlers.set(event, handler),
			getFlag: () => "private",
			setModel: async (model: unknown) => {
				selected.push(model);
				return true;
			},
		} as any;
		const ctx = {
			cwd: "/home/dev/code/private/project",
			modelRegistry: { find: () => localModel },
			ui: { theme, setStatus: () => undefined, notify: () => undefined },
		} as any;

		inferenceRouter(pi);
		await handlers.get("session_start")?.({}, ctx);
		expect(selected).toEqual([localModel]);
	});

	test("leaves authority rendering to the common footer", async () => {
		const previous = process.env.WORKBENCH_PI_MODE;
		process.env.WORKBENCH_PI_MODE = "hosted-unrestricted";
		try {
			const handlers = new Map<string, (...args: any[]) => any>();
			const statuses: string[] = [];
			const frontierModel = { provider: "openai-codex", id: "frontier" };
			const pi = {
				registerFlag: () => undefined,
				registerCommand: () => undefined,
				on: (event: string, handler: (...args: any[]) => any) => handlers.set(event, handler),
				getFlag: () => "frontier",
				setModel: async () => true,
			} as any;
			const ctx = {
				cwd: "/home/dev/code/project",
				modelRegistry: { find: () => frontierModel },
				ui: {
					theme,
					setStatus: (_name: string, value: string) => statuses.push(value),
					notify: () => undefined,
				},
			} as any;

			inferenceRouter(pi);
			await handlers.get("session_start")?.({}, ctx);
			expect(statuses).toEqual([]);
		} finally {
			if (previous === undefined) delete process.env.WORKBENCH_PI_MODE;
			else process.env.WORKBENCH_PI_MODE = previous;
		}
	});

	test("fails closed when the selected private model is unavailable", async () => {
		const previous = process.env.WORKBENCH_PI_MODE;
		delete process.env.WORKBENCH_PI_MODE;
		try {
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
			expect(notifications.at(-1)).toContain("Private route blocked");
		} finally {
			if (previous === undefined) delete process.env.WORKBENCH_PI_MODE;
			else process.env.WORKBENCH_PI_MODE = previous;
		}
	});
});

test("pins local-restricted against route flags and rejects later cloud model selection", async () => {
	const previous = process.env.WORKBENCH_PI_MODE;
	process.env.WORKBENCH_PI_MODE = "local-restricted";
	try {
		const handlers = new Map<string, (...args: any[]) => any>();
		const commands = new Map<string, any>();
		const selected: string[] = [];
		const ctx = {
			cwd: "/tmp/example",
			model: { provider: "openai-codex" },
			modelRegistry: { find: (provider: string) => ({ provider, id: "model" }) },
			ui: { theme, setStatus() {}, notify() {}, setEditorText() {} },
		} as any;
		inferenceRouter({
			registerFlag() {},
			registerCommand: (name: string, command: any) => commands.set(name, command),
			on: (name: string, handler: any) => handlers.set(name, handler),
			getFlag: () => "frontier",
			setModel: async (model: any) => {
				selected.push(model.provider);
				ctx.model = model;
				return true;
			},
		} as any);
		await handlers.get("session_start")?.({}, ctx);
		expect(selected).toEqual(["omlx"]);
		await commands.get("route").handler("frontier", ctx);
		expect(selected).toEqual(["omlx"]);
		ctx.model = { provider: "openai-codex" };
		await handlers.get("model_select")?.({ model: ctx.model }, ctx);
		expect(ctx.model.provider).toBe("omlx");
	} finally {
		if (previous === undefined) delete process.env.WORKBENCH_PI_MODE;
		else process.env.WORKBENCH_PI_MODE = previous;
	}
});

test("invalid private routing config blocks every input source", async () => {
	const cwd = mkdtempSync(join(tmpdir(), "wb-router-"));
	mkdirSync(join(cwd, ".pi"));
	writeFileSync(
		join(cwd, ".pi/inference-router.json"),
		JSON.stringify({ private: { provider: "openai-codex" } }),
	);
	const handlers = new Map<string, any>();
	let sends = 0;
	const ctx = {
		cwd,
		modelRegistry: { find: () => ({ provider: "openai-codex" }) },
		ui: { theme, setStatus() {}, notify() {}, setEditorText() {} },
	} as any;
	inferenceRouter({
		registerFlag() {},
		registerCommand() {},
		on: (event: string, handler: any) => handlers.set(event, handler),
		getFlag: () => "private",
		setModel: async () => {
			sends++;
			return true;
		},
	} as any);
	await handlers.get("session_start")({}, ctx);
	expect(sends).toBe(0);
	for (const source of ["user", "extension"]) {
		expect(await handlers.get("input")({ source, text: "private" }, ctx)).toEqual({ action: "handled" });
	}
	expect(sends).toBe(0);
});

test("preserves a compatible explicit startup model for hosted and local profiles", async () => {
	const previous = process.env.WORKBENCH_PI_MODE;
	try {
		for (const [mode, provider, id] of [
			["hosted-restricted", "openai-codex", "gpt-5.6-terra"],
			["hosted-unrestricted", "anthropic", "chosen-cloud-model"],
			["local-restricted", "omlx", "chosen-local-model"],
		]) {
			process.env.WORKBENCH_PI_MODE = mode;
			const handlers = new Map<string, any>();
			const selected: unknown[] = [];
			const ctx = {
				cwd: "/tmp/example",
				model: { provider, id },
				modelRegistry: { find: () => ({ provider, id: "configured-default" }) },
				ui: { theme, setStatus() {}, notify() {}, setEditorText() {} },
			} as any;
			inferenceRouter({
				registerFlag() {},
				registerCommand() {},
				on: (event: string, handler: any) => handlers.set(event, handler),
				getFlag: () => "frontier",
				setModel: async (model: unknown) => {
					selected.push(model);
					return true;
				},
			} as any);
			await handlers.get("session_start")({}, ctx);
			expect(selected).toEqual([]);
			expect(await handlers.get("input")({ source: "user", text: "synthetic" }, ctx)).toEqual({
				action: "continue",
			});
		}
	} finally {
		if (previous === undefined) delete process.env.WORKBENCH_PI_MODE;
		else process.env.WORKBENCH_PI_MODE = previous;
	}
});
