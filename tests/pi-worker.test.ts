import { describe, expect, mock, test } from "bun:test";
import { buildWorkerPrompt, reviewInstructions, workerSlug } from "../agents/pi/extensions/lib/worker-core";

mock.module("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Optional: schema } };
});

const { default: workerExtension } = await import("../agents/pi/extensions/worker");

describe("Pi worker delegate", () => {
	test("derives a bounded branch slug from the task", () => {
		expect(workerSlug("Fix the flaky footer test in CI!", "202607220101")).toBe(
			"fix-the-flaky-footer-202607220101",
		);
		expect(workerSlug("!!!", "202607220101")).toBe("task-202607220101");
	});

	test("worker prompt forbids git mutation and requires verification", () => {
		const prompt = buildWorkerPrompt("add a test", "worker/add-a-test-x");
		expect(prompt).toContain("worker/add-a-test-x");
		expect(prompt).toContain("Do not run git commit");
		expect(prompt).toContain("leave all changes uncommitted");
		expect(prompt).toContain("tests or checks");
	});

	test("review instructions keep adoption and cleanup with the parent", () => {
		const text = reviewInstructions("/tmp/x.worktree", "worker/x");
		expect(text).toContain("git -C /tmp/x.worktree diff");
		expect(text).toContain("Adopt useful changes in the parent checkout");
		expect(text).toContain("action=discard");
		expect(text).not.toContain("git push");
	});

	test("discard reports a branch deletion failure instead of claiming full cleanup", async () => {
		let workerTool:
			| {
					execute: (...args: unknown[]) => Promise<{ content: { text: string }[]; isError?: boolean }>;
			  }
			| undefined;
		const root = `/tmp/wb-worker-${Date.now()}`;
		const pi = {
			registerTool(tool: typeof workerTool) {
				workerTool = tool;
			},
			registerCommand() {},
			async exec(command: string, args: string[]) {
				if (command === "pi") return { code: 0, stdout: "done", stderr: "" };
				if (args.includes("--show-toplevel")) return { code: 0, stdout: `${root}\n`, stderr: "" };
				if (args[0] === "status" || args[0] === "diff") return { code: 0, stdout: "", stderr: "" };
				if (args[0] === "branch") return { code: 1, stdout: "", stderr: "branch is locked" };
				return { code: 0, stdout: "", stderr: "" };
			},
		};
		workerExtension(pi as never);
		const ctx = { cwd: root };

		await workerTool?.execute(
			"delegate",
			{ action: "delegate", task: "add one test" },
			undefined,
			undefined,
			ctx,
		);
		const discarded = await workerTool?.execute("discard", { action: "discard" }, undefined, undefined, ctx);

		expect(discarded?.isError).toBe(true);
		expect(discarded?.content[0]?.text).toContain("but branch deletion failed");
	});
});
