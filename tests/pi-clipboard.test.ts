import { describe, expect, mock, test } from "bun:test";

mock.module("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema } };
});

const { copyAndVerifyPlainText } = await import("../agents/pi/extensions/clipboard");

describe("Pi clipboard", () => {
	test("copies plain text and verifies the exact clipboard value", async () => {
		const calls: Array<{ command: string; input?: string }> = [];
		const run = async (command: string, input?: string) => {
			calls.push({ command, input });
			return command === "pbpaste" ? "Hello\n\nWorld" : "";
		};

		await expect(copyAndVerifyPlainText("Hello\n\nWorld", run)).resolves.toBeUndefined();
		expect(calls).toEqual([
			{ command: "pbcopy", input: "Hello\n\nWorld" },
			{ command: "pbpaste", input: undefined },
		]);
	});

	test("fails closed when clipboard verification differs", async () => {
		const run = async (command: string) => (command === "pbpaste" ? "different" : "");
		await expect(copyAndVerifyPlainText("expected", run)).rejects.toThrow("Clipboard verification failed");
	});
});
