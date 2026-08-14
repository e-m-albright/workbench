import { describe, expect, mock, test } from "bun:test";

mock.module("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Optional: schema, Array: schema } };
});

const module = await import("../agents/pi/extensions/github-workflow-dispatch");
const { buildDispatchArgs, confirmationText, newestRunUrl, validateDispatch } = module;

const dispatch = {
	repository: "e-m-albright/evan",
	workflow: "digest.yml",
	ref: "main",
	inputs: [
		{ name: "date", value: "2026-08-10" },
		{ name: "dry_run", value: "false" },
	],
};

describe("GitHub workflow dispatch", () => {
	test("builds an argv-only gh dispatch with explicit inputs", () => {
		expect(buildDispatchArgs(dispatch)).toEqual([
			"workflow",
			"run",
			"digest.yml",
			"--repo",
			"e-m-albright/evan",
			"--ref",
			"main",
			"--field",
			"date=2026-08-10",
			"--field",
			"dry_run=false",
		]);
	});

	test("shows every outward-facing parameter in the confirmation", () => {
		const text = confirmationText(dispatch);
		expect(text).toContain("Repository: e-m-albright/evan");
		expect(text).toContain("Workflow: digest.yml");
		expect(text).toContain("Ref: main");
		expect(text).toContain("date=2026-08-10");
		expect(text).toContain("dry_run=false");
	});

	test("rejects flag-shaped and malformed identifiers", () => {
		expect(() => validateDispatch({ ...dispatch, repository: "evan" })).toThrow("owner/name");
		expect(() => validateDispatch({ ...dispatch, workflow: "--help" })).toThrow("workflow");
		expect(() => validateDispatch({ ...dispatch, ref: "--help" })).toThrow("ref");
		expect(() =>
			validateDispatch({ ...dispatch, inputs: [{ name: "bad name", value: "x" }] }),
		).toThrow("input name");
	});

	test("requires confirmation, dispatches once, and returns the created run URL", async () => {
		let tool: any;
		const exec = mock(async (_command: string, args: string[]) => {
			if (args[0] === "workflow") return { code: 0, stdout: "", stderr: "" };
			return {
				code: 0,
				stdout: JSON.stringify([{ createdAt: new Date().toISOString(), url: "https://github.test/run/1" }]),
				stderr: "",
			};
		});
		module.default({ registerTool: (value: any) => (tool = value), exec } as any);
		const confirm = mock(async () => true);

		const result = await tool.execute(
			"call-1",
			dispatch,
			undefined,
			undefined,
			{ hasUI: true, ui: { confirm } },
		);

		expect(confirm).toHaveBeenCalledTimes(1);
		expect(exec).toHaveBeenCalledTimes(2);
		expect(result.details.runUrl).toBe("https://github.test/run/1");
	});

	test("returns only a newly created workflow-dispatch run URL", () => {
		const now = Date.parse("2026-08-14T22:00:00Z");
		const payload = JSON.stringify([
			{ createdAt: "2026-08-14T21:00:00Z", url: "https://github.test/old" },
			{ createdAt: "2026-08-14T22:00:01Z", url: "https://github.test/new" },
		]);
		expect(newestRunUrl(payload, now)).toBe("https://github.test/new");
		expect(newestRunUrl("not-json", now)).toBeUndefined();
	});
});
