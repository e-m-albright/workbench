import { describe, expect, mock, test } from "bun:test";
import { buildWorkerPrompt, reviewInstructions, workerSlug } from "../agents/pi/extensions/lib/worker-core";

mock.module("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Optional: schema } };
});

const { default: workerExtension } = await import("../agents/pi/extensions/worker");

type ToolResult = { content: { text: string }[]; details?: Record<string, unknown> };
type WorkerTool = {
	execute: (...args: unknown[]) => Promise<ToolResult>;
};

type ExecResult = { code: number; stdout: string; stderr: string; killed: boolean };

function deferred<T>() {
	let resolve!: (value: T) => void;
	const promise = new Promise<T>((done) => {
		resolve = done;
	});
	return { promise, resolve };
}

function createHarness(run: Promise<ExecResult>, options: { branchDeleteFails?: boolean } = {}) {
	let workerTool: WorkerTool | undefined;
	let shutdown: ((event: unknown, ctx: any) => Promise<void>) | undefined;
	let workerSignal: AbortSignal | undefined;
	const statuses: Array<string | undefined> = [];
	const notifications: Array<{ text: string; level: string }> = [];
	const root = `/tmp/wb-worker-${Date.now()}-${Math.random()}`;
	const pi = {
		registerTool(tool: WorkerTool) {
			workerTool = tool;
		},
		registerCommand() {},
		on(event: string, handler: typeof shutdown) {
			if (event === "session_shutdown") shutdown = handler;
		},
		async exec(command: string, args: string[], execOptions?: { signal?: AbortSignal }) {
			if (command === "pi") {
				workerSignal = execOptions?.signal;
				return run;
			}
			if (args.includes("--show-toplevel")) {
				return { code: 0, stdout: `${root}\n`, stderr: "", killed: false };
			}
			if (args[0] === "status" || args[0] === "diff") {
				return { code: 0, stdout: "", stderr: "", killed: false };
			}
			if (args[0] === "branch" && options.branchDeleteFails) {
				return { code: 1, stdout: "", stderr: "branch is locked", killed: false };
			}
			return { code: 0, stdout: "", stderr: "", killed: false };
		},
	};
	workerExtension(pi as never);
	const ctx = {
		cwd: root,
		hasUI: true,
		ui: {
			setStatus(_key: string, value: string | undefined) {
				statuses.push(value);
			},
			notify(text: string, level: string) {
				notifications.push({ text, level });
			},
		},
	};
	return {
		get tool() {
			return workerTool;
		},
		shutdown,
		ctx,
		statuses,
		notifications,
		get workerSignal() {
			return workerSignal;
		},
	};
}

async function invoke(tool: WorkerTool | undefined, action: string, task?: string): Promise<ToolResult> {
	if (!tool) throw new Error("worker tool was not registered");
	return tool.execute("call", { action, task }, undefined, undefined, {});
}

async function settleBackground(): Promise<void> {
	await Promise.resolve();
	await new Promise((resolve) => setTimeout(resolve, 0));
}

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

	test("delegate returns immediately while the child continues in the background", async () => {
		const child = deferred<ExecResult>();
		const harness = createHarness(child.promise);
		const started = await harness.tool?.execute(
			"delegate",
			{ action: "delegate", task: "add one test" },
			undefined,
			undefined,
			harness.ctx,
		);

		expect(started?.content[0]?.text).toContain("started in the background");
		expect(started?.details?.status).toBe("running");
		expect(harness.statuses.at(-1)).toContain("worker running");

		const progress = await harness.tool?.execute(
			"review",
			{ action: "review" },
			undefined,
			undefined,
			harness.ctx,
		);
		expect(progress?.content[0]?.text).toContain("Worker running");

		child.resolve({ code: 0, stdout: "implemented and tested", stderr: "", killed: false });
		await settleBackground();

		const finished = await harness.tool?.execute(
			"review",
			{ action: "review" },
			undefined,
			undefined,
			harness.ctx,
		);
		expect(finished?.content[0]?.text).toContain("Worker report:\nimplemented and tested");
		expect(harness.statuses.at(-1)).toContain("worker done");
		expect(harness.notifications.at(-1)).toEqual({
			text: expect.stringContaining("Worker finished"),
			level: "info",
		});

		await harness.tool?.execute("discard", { action: "discard" }, undefined, undefined, harness.ctx);
	});

	test("failed background work becomes a real tool error on review", async () => {
		const child = deferred<ExecResult>();
		const harness = createHarness(child.promise);
		await harness.tool?.execute(
			"delegate",
			{ action: "delegate", task: "add one test" },
			undefined,
			undefined,
			harness.ctx,
		);
		child.resolve({ code: 143, stdout: "partial", stderr: "timed out", killed: true });
		await settleBackground();

		await expect(
			harness.tool?.execute("review", { action: "review" }, undefined, undefined, harness.ctx),
		).rejects.toThrow("Worker failed (exit 143)");
		expect(harness.statuses.at(-1)).toContain("worker failed");
		expect(harness.notifications.at(-1)?.level).toBe("error");

		await harness.tool?.execute("discard", { action: "discard" }, undefined, undefined, harness.ctx);
	});

	test("session shutdown aborts a running child and clears its status", async () => {
		const child = deferred<ExecResult>();
		const harness = createHarness(child.promise);
		await harness.tool?.execute(
			"delegate",
			{ action: "delegate", task: "add one test" },
			undefined,
			undefined,
			harness.ctx,
		);

		expect(harness.workerSignal?.aborted).toBe(false);
		await harness.shutdown?.({}, harness.ctx);
		expect(harness.workerSignal?.aborted).toBe(true);
		expect(harness.statuses.at(-1)).toBeUndefined();
	});

	test("discard reports a branch deletion failure instead of claiming full cleanup", async () => {
		const harness = createHarness(Promise.resolve({ code: 0, stdout: "done", stderr: "", killed: false }), {
			branchDeleteFails: true,
		});
		await harness.tool?.execute(
			"delegate",
			{ action: "delegate", task: "add one test" },
			undefined,
			undefined,
			harness.ctx,
		);
		await settleBackground();

		await expect(
			harness.tool?.execute("discard", { action: "discard" }, undefined, undefined, harness.ctx),
		).rejects.toThrow("but branch deletion failed");
	});
});
