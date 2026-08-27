import { describe, expect, test } from "bun:test";
import { buildWorkerPrompt, reviewInstructions, workerSlug } from "../agents/pi/extensions/worker-core";

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
});
