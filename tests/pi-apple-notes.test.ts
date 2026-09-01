import { describe, expect, mock, test } from "bun:test";

mock.module("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Optional: schema, Number: schema } };
});

const { default: appleNotesExtension } = await import("../agents/pi/extensions/apple-notes");

type RegisteredTool = {
	name: string;
	execute: (...args: unknown[]) => Promise<unknown>;
};

function registeredTools() {
	const tools = new Map<string, RegisteredTool>();
	let execCalls = 0;
	appleNotesExtension({
		registerTool(tool: RegisteredTool) {
			tools.set(tool.name, tool);
		},
		async exec() {
			execCalls++;
			return { code: 0, stdout: "{}", stderr: "" };
		},
	} as never);
	return { tools, execCalls: () => execCalls };
}

describe("Apple Notes write boundary", () => {
	test("refuses a create in headless mode before invoking the bridge CLI", async () => {
		const { tools, execCalls } = registeredTools();
		const create = tools.get("apple_notes_create");

		await expect(
			create?.execute("call", { title: "Plan", body: "One item" }, undefined, undefined, { hasUI: false }),
		).rejects.toThrow("interactive confirmation");
		expect(execCalls()).toBe(0);
	});
});
