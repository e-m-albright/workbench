import { execFileSync, spawnSync } from "node:child_process";
import {
	existsSync,
	mkdirSync,
	mkdtempSync,
	realpathSync,
	rmSync,
	symlinkSync,
	writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { buildWorkerPrompt, reviewInstructions, workerSlug } from "../agents/pi/extensions/lib/worker-core";

vi.doMock("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Optional: schema } };
});

const { default: workerExtension } = await import("../agents/pi/extensions/worker");

beforeEach(() => {
	vi.stubEnv("PI_CODING_AGENT_DIR", "/nonexistent-workbench-test-agent");
	vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", undefined);
	vi.stubEnv("WORKBENCH_PI_MODE", undefined);
});
afterEach(() => {
	vi.unstubAllEnvs();
});

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

function createHarness(
	run: Promise<ExecResult>,
	options: {
		branchDeleteFails?: boolean;
		parentStatus?: string;
		provider?: string;
		model?: string;
		thinking?: string;
		workerChild?: boolean;
		root?: string;
		git?: (args: string[], cwd: string) => ExecResult;
	} = {},
) {
	let workerTool: WorkerTool | undefined;
	let shutdown: ((event: unknown, ctx: any) => Promise<void>) | undefined;
	let workerSignal: AbortSignal | undefined;
	let workerArgs: string[] | undefined;
	let workerTimeout: number | undefined;
	const calls: string[][] = [];
	const statuses: Array<string | undefined> = [];
	const notifications: Array<{ text: string; level: string }> = [];
	const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
	const root = options.root ?? `/tmp/wb-worker-${Date.now()}-${Math.random()}`;
	const pi = {
		registerTool(tool: WorkerTool) {
			workerTool = tool;
		},
		registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) {
			commands.set(name, command);
		},
		registerFlag() {},
		getFlag: () => options.workerChild,
		getThinkingLevel: () => options.thinking ?? "medium",
		on(event: string, handler: typeof shutdown) {
			if (event === "session_shutdown") shutdown = handler;
		},
		async exec(
			command: string,
			args: string[],
			execOptions?: { signal?: AbortSignal; timeout?: number; cwd?: string },
		) {
			calls.push([command, ...args]);
			if (command === "pi") {
				workerTimeout = execOptions?.timeout;
				workerSignal = execOptions?.signal;
				workerArgs = args;
				return run;
			}
			if (options.git) return options.git(args, execOptions?.cwd ?? root);
			if (args.includes("--show-toplevel")) {
				return { code: 0, stdout: `${root}\n`, stderr: "", killed: false };
			}
			if (args[0] === "rev-parse") {
				return { code: 0, stdout: `${"a".repeat(40)}\n`, stderr: "", killed: false };
			}
			if (args[0] === "rev-list") {
				return { code: 0, stdout: "0\n", stderr: "", killed: false };
			}
			if (args[0] === "symbolic-ref") {
				const branch = calls.find((call) => call[1] === "worktree" && call[2] === "add")?.[4];
				return { code: 0, stdout: `refs/heads/${branch}\n`, stderr: "", killed: false };
			}
			if (args[0] === "status" || args[0] === "diff") {
				return {
					code: 0,
					stdout: args[0] === "status" ? (options.parentStatus ?? "") : "",
					stderr: "",
					killed: false,
				};
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
		model: { provider: options.provider ?? "openai-codex", id: options.model ?? "selected-model" },
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
		calls,
		commands,
		get workerTimeout() {
			return workerTimeout;
		},
		notifications,
		get workerSignal() {
			return workerSignal;
		},
		get workerArgs() {
			return workerArgs;
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

const managedHomes: string[] = [];
function gitFixture() {
	const home = realpathSync(mkdtempSync(join(tmpdir(), "wb-worker-git-")));
	managedHomes.push(home);
	const root = join(home, "parent");
	mkdirSync(root);
	const env = {
		...process.env,
		GIT_CONFIG_GLOBAL: "/dev/null",
		GIT_CONFIG_NOSYSTEM: "1",
		GIT_AUTHOR_NAME: "Worker Test",
		GIT_AUTHOR_EMAIL: "worker@example.invalid",
		GIT_COMMITTER_NAME: "Worker Test",
		GIT_COMMITTER_EMAIL: "worker@example.invalid",
	};
	const git = (args: string[], cwd = root) =>
		execFileSync("git", args, { cwd, env, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
	git(["init", "-q", "-b", "main"]);
	for (const file of ["committed.txt", "staged.txt", "unstaged.txt"]) {
		writeFileSync(join(root, file), "initial\n");
	}
	git(["add", "."]);
	git(["commit", "-qm", "initial"]);
	const runGit = (args: string[], cwd: string): ExecResult => {
		const result = spawnSync("git", args, { cwd, env, encoding: "utf8" });
		return {
			code: result.status ?? 1,
			stdout: result.stdout ?? "",
			stderr: result.error?.message ?? result.stderr ?? "",
			killed: result.signal !== null,
		};
	};
	return { root, git, runGit };
}

async function startGitWorker(override?: (args: string[], cwd: string) => ExecResult | undefined) {
	const fixture = gitFixture();
	const harness = createHarness(Promise.resolve({ code: 0, stdout: "done", stderr: "", killed: false }), {
		root: fixture.root,
		git: (args, cwd) => override?.(args, cwd) ?? fixture.runGit(args, cwd),
	});
	const started = await harness.tool?.execute(
		"delegate",
		{ action: "delegate", task: "produce changes" },
		undefined,
		undefined,
		harness.ctx,
	);
	await settleBackground();
	return {
		...fixture,
		harness,
		dir: String(started?.details?.dir),
		branch: String(started?.details?.branch),
	};
}

function managedRepo(parent: string): string {
	const home = realpathSync(mkdtempSync(join(tmpdir(), "wb-worker-managed-")));
	managedHomes.push(home);
	vi.stubEnv("WORKBENCH_HOST_HOME", home);
	const root = join(home, parent, "project");
	mkdirSync(join(root, ".git"), { recursive: true });
	return root;
}
afterEach(() => {
	for (const home of managedHomes.splice(0)) rmSync(home, { recursive: true, force: true });
});

describe("Pi worker delegate", () => {
	test("manual force cleanup explicitly reports discarded unique commits", async () => {
		const worker = await startGitWorker();
		writeFileSync(join(worker.dir, "committed.txt"), "deliberately rejected\n");
		worker.git(["add", "committed.txt"], worker.dir);
		worker.git(["commit", "-qm", "rejected commit"], worker.dir);
		writeFileSync(join(worker.dir, "untracked.txt"), "also rejected\n");
		await worker.harness.commands.get("worker-done")?.handler("--force", worker.harness.ctx);
		expect(existsSync(worker.dir)).toBe(false);
		expect(
			worker.runGit(["show-ref", "--verify", "--quiet", `refs/heads/${worker.branch}`], worker.root).code,
		).toBe(1);
		expect(worker.harness.notifications.at(-1)?.text).toContain(
			"discarded 1 commit not reachable from the parent",
		);
	});

	test.each([
		["review", "status"],
		["review", "diff"],
		["review", "log"],
		["discard", "status"],
		["discard", "rev-parse"],
		["discard", "rev-list"],
		["discard", "symbolic-ref"],
	])("%s preserves output when Git %s inspection fails", async (action, command) => {
		let fail = false;
		const worker = await startGitWorker((args) =>
			fail && args[0] === command
				? { code: 128, stdout: "", stderr: "inspection unavailable", killed: false }
				: undefined,
		);
		fail = true;
		await expect(
			worker.harness.tool?.execute(
				"inspect",
				{ action, disposition: "rejected" },
				undefined,
				undefined,
				worker.harness.ctx,
			),
		).rejects.toThrow("Could not inspect worker");
		expect(existsSync(worker.dir)).toBe(true);
		expect(worker.harness.calls.some((call) => call[1] === "worktree" && call[2] === "remove")).toBe(false);
	});

	test("a child worker cannot recursively delegate or create Git state", async () => {
		const harness = createHarness(Promise.resolve({ code: 0, stdout: "done", stderr: "", killed: false }), {
			workerChild: true,
		});
		await expect(
			harness.tool?.execute(
				"delegate",
				{ action: "delegate", task: "another child" },
				undefined,
				undefined,
				harness.ctx,
			),
		).rejects.toThrow("cannot delegate");
		expect(harness.calls).toEqual([]);
	});

	test("worker inherits the parent's selected provider, model, and thinking effort", async () => {
		const harness = createHarness(Promise.resolve({ code: 0, stdout: "done", stderr: "", killed: false }), {
			provider: "anthropic",
			model: "selected-review-model",
			thinking: "high",
		});
		await harness.tool?.execute(
			"delegate",
			{ action: "delegate", task: "one task" },
			undefined,
			undefined,
			harness.ctx,
		);
		for (const [flag, value] of [
			["--provider", "anthropic"],
			["--model", "selected-review-model"],
			["--thinking", "high"],
		]) {
			const index = harness.workerArgs?.indexOf(flag) ?? -1;
			expect(index).toBeGreaterThanOrEqual(0);
			expect(harness.workerArgs?.[index + 1]).toBe(value);
		}
		expect(harness.workerArgs).toContain("--worker-child");
		await settleBackground();
	});

	test.each(["other branch", "detached HEAD"])("cleanup preserves a worker moved to %s", async (mode) => {
		const worker = await startGitWorker();
		worker.git(
			mode === "other branch" ? ["switch", "-qc", "unexpected"] : ["switch", "-q", "--detach"],
			worker.dir,
		);
		await expect(
			worker.harness.tool?.execute(
				"discard",
				{ action: "discard", disposition: "rejected" },
				undefined,
				undefined,
				worker.harness.ctx,
			),
		).rejects.toThrow(/branch changed|Could not inspect worker/);
		expect(existsSync(worker.dir)).toBe(true);
		expect(
			worker.runGit(["show-ref", "--verify", "--quiet", `refs/heads/${worker.branch}`], worker.root).code,
		).toBe(0);
	});

	test("even parent-reachable worker commits need a deliberate disposition", async () => {
		const worker = await startGitWorker();
		writeFileSync(join(worker.dir, "committed.txt"), "adopted result\n");
		worker.git(["add", "committed.txt"], worker.dir);
		worker.git(["commit", "-qm", "adopted result"], worker.dir);
		worker.git(["merge", "--ff-only", worker.branch]);
		await expect(
			worker.harness.tool?.execute(
				"discard",
				{ action: "discard" },
				undefined,
				undefined,
				worker.harness.ctx,
			),
		).rejects.toThrow("HEAD changed");
		expect(existsSync(worker.dir)).toBe(true);
		await worker.harness.tool?.execute(
			"discard",
			{ action: "discard", disposition: "adopted" },
			undefined,
			undefined,
			worker.harness.ctx,
		);
		expect(existsSync(worker.dir)).toBe(false);
		expect(worker.git(["log", "-1", "--format=%s"])).toBe("adopted result");
	});

	test.each(["adopted", "rejected"])(
		"dirty worker output needs an explicit %s disposition before cleanup",
		async (disposition) => {
			const worker = await startGitWorker();
			writeFileSync(join(worker.dir, "unstaged.txt"), "finished result\n");
			writeFileSync(join(worker.dir, "untracked.txt"), "new result\n");
			await expect(
				worker.harness.tool?.execute(
					"discard",
					{ action: "discard" },
					undefined,
					undefined,
					worker.harness.ctx,
				),
			).rejects.toThrow("disposition");
			expect(existsSync(worker.dir)).toBe(true);
			await worker.harness.tool?.execute(
				"discard",
				{ action: "discard", disposition },
				undefined,
				undefined,
				worker.harness.ctx,
			);
			expect(existsSync(worker.dir)).toBe(false);
			expect(
				worker.runGit(["show-ref", "--verify", "--quiet", `refs/heads/${worker.branch}`], worker.root).code,
			).toBe(1);
		},
	);

	test("discard preserves a clean worktree containing commits absent from the parent", async () => {
		const worker = await startGitWorker();
		writeFileSync(join(worker.dir, "committed.txt"), "unique result\n");
		worker.git(["add", "committed.txt"], worker.dir);
		worker.git(["commit", "-qm", "unique result"], worker.dir);
		const commit = worker.git(["rev-parse", "HEAD"], worker.dir);
		for (const disposition of [undefined, "adopted", "rejected"]) {
			await expect(
				worker.harness.tool?.execute(
					"discard",
					{ action: "discard", disposition },
					undefined,
					undefined,
					worker.harness.ctx,
				),
			).rejects.toThrow("commits not reachable from the parent");
			expect(existsSync(worker.dir)).toBe(true);
			expect(worker.git(["rev-parse", worker.branch])).toBe(commit);
		}
	});

	test("review includes committed, staged, unstaged, and untracked output from its starting commit", async () => {
		const fixture = gitFixture();
		const base = fixture.git(["rev-parse", "HEAD"]);
		const harness = createHarness(Promise.resolve({ code: 0, stdout: "done", stderr: "", killed: false }), {
			root: fixture.root,
			git: fixture.runGit,
		});
		const started = await harness.tool?.execute(
			"delegate",
			{ action: "delegate", task: "produce changes" },
			undefined,
			undefined,
			harness.ctx,
		);
		const dir = String(started?.details?.dir);
		writeFileSync(join(dir, "committed.txt"), "committed result\n");
		fixture.git(["add", "committed.txt"], dir);
		fixture.git(["commit", "-qm", "unexpected worker commit"], dir);
		writeFileSync(join(dir, "staged.txt"), "staged result\n");
		fixture.git(["add", "staged.txt"], dir);
		writeFileSync(join(dir, "unstaged.txt"), "unstaged result\n");
		writeFileSync(join(dir, "untracked.txt"), "new result\n");
		await settleBackground();

		const reviewed = await harness.tool?.execute(
			"review",
			{ action: "review" },
			undefined,
			undefined,
			harness.ctx,
		);
		const text = reviewed?.content[0]?.text;
		for (const expected of ["committed.txt", "staged.txt", "unstaged.txt", "untracked.txt", base]) {
			expect(text).toContain(expected);
		}
		expect(text).toContain("unexpected worker commit");
	});

	test("managed delegation permits a sibling worktree under public code", async () => {
		vi.stubEnv("WORKBENCH_PI_MODE", "hosted-managed");
		vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "managed");
		const harness = createHarness(Promise.resolve({ code: 0, stdout: "", stderr: "", killed: false }), {
			root: managedRepo("code/public"),
		});
		await harness.tool?.execute(
			"delegate",
			{ action: "delegate", task: "test" },
			undefined,
			undefined,
			harness.ctx,
		);
		expect(harness.calls.some((call) => call[0] === "pi")).toBe(true);
		const add = harness.calls.find((call) => call[1] === "worktree" && call[2] === "add");
		expect(add?.[5]).toContain("/code/public/");
		await settleBackground();
		await harness.tool?.execute("discard", { action: "discard" }, undefined, undefined, harness.ctx);
	});

	test.each(["Desktop", "Downloads"])(
		"managed delegation permits sibling worktrees under %s",
		async (parent) => {
			vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "managed");
			const harness = createHarness(Promise.resolve({ code: 0, stdout: "", stderr: "", killed: false }), {
				root: managedRepo(parent),
			});
			await harness.tool?.execute(
				"delegate",
				{ action: "delegate", task: "test" },
				undefined,
				undefined,
				harness.ctx,
			);
			expect(harness.calls.some((call) => call[0] === "pi")).toBe(true);
			await settleBackground();
		},
	);

	test("managed private checkout rejects sibling placement before any Git mutation", async () => {
		vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "managed");
		const harness = createHarness(Promise.resolve({ code: 0, stdout: "", stderr: "", killed: false }), {
			root: managedRepo("code/private"),
		});
		await expect(
			harness.tool?.execute(
				"delegate",
				{ action: "delegate", task: "test" },
				undefined,
				undefined,
				harness.ctx,
			),
		).rejects.toThrow("outside managed write roots");
		expect(harness.calls.some((call) => call.includes("worktree") || call[0] === "pi")).toBe(false);
	});

	test.each(["file", "symlink"])("managed worker rejects a %s .git before mutating Git", async (kind) => {
		vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "managed");
		const root = managedRepo("code/public");
		rmSync(join(root, ".git"), { recursive: true });
		if (kind === "file") writeFileSync(join(root, ".git"), "gitdir: ../outside");
		else symlinkSync(join(root, ".."), join(root, ".git"));
		const harness = createHarness(Promise.resolve({ code: 0, stdout: "", stderr: "", killed: false }), {
			root,
		});
		await expect(
			harness.tool?.execute(
				"delegate",
				{ action: "delegate", task: "test" },
				undefined,
				undefined,
				harness.ctx,
			),
		).rejects.toThrow("ordinary checkout");
		expect(harness.calls.some((call) => call.includes("worktree") || call[0] === "pi")).toBe(false);
	});

	test("rejects delegation when the parent has tracked or untracked changes", async () => {
		const harness = createHarness(Promise.resolve({ code: 0, stdout: "", stderr: "", killed: false }), {
			parentStatus: " M tracked.ts\n?? untracked.ts\n",
		});

		await expect(
			harness.tool?.execute(
				"delegate",
				{ action: "delegate", task: "test" },
				undefined,
				undefined,
				harness.ctx,
			),
		).rejects.toThrow("clean parent working tree");
		expect(harness.calls).toContainEqual(["git", "status", "--porcelain"]);
		expect(harness.calls.some((call) => call.includes("worktree"))).toBe(false);
		expect(harness.calls.some((call) => call[0] === "pi")).toBe(false);
	});

	test("continues delegation when the parent working tree is clean", async () => {
		const child = deferred<ExecResult>();
		const harness = createHarness(child.promise);

		await harness.tool?.execute(
			"delegate",
			{ action: "delegate", task: "test" },
			undefined,
			undefined,
			harness.ctx,
		);

		const statusIndex = harness.calls.findIndex((call) => call[1] === "status");
		const worktreeIndex = harness.calls.findIndex((call) => call.includes("worktree"));
		expect(statusIndex).toBeGreaterThanOrEqual(0);
		expect(worktreeIndex).toBeGreaterThan(statusIndex);
		expect(harness.calls.some((call) => call[0] === "pi")).toBe(true);

		child.resolve({ code: 0, stdout: "done", stderr: "", killed: false });
		await settleBackground();
		await harness.tool?.execute("discard", { action: "discard" }, undefined, undefined, harness.ctx);
	});

	test("worker uses its configured timeout without an undocumented settings manager", async () => {
		const agent = mkdtempSync(join(tmpdir(), "pi-worker-settings-"));
		writeFileSync(join(agent, "settings.json"), JSON.stringify({ worker: { timeoutMs: 3210 } }));
		vi.stubEnv("PI_CODING_AGENT_DIR", agent);
		const harness = createHarness(Promise.resolve({ code: 0, stdout: "", stderr: "", killed: false }));
		try {
			await harness.tool?.execute(
				"delegate",
				{ action: "delegate", task: "test" },
				undefined,
				undefined,
				harness.ctx,
			);
			expect(harness.workerTimeout).toBe(3210);
		} finally {
			await harness.shutdown?.({}, harness.ctx);
			rmSync(agent, { recursive: true, force: true });
		}
	});
	test("derives a bounded branch slug from the task", () => {
		expect(workerSlug("Fix the flaky footer test in CI!", "202607220101")).toBe(
			"fix-the-flaky-footer-202607220101",
		);
		expect(workerSlug("!!!", "202607220101")).toBe("task-202607220101");
	});

	test("pins each worker to its parent's privacy route", async () => {
		for (const [provider, route] of [
			["openai-codex", "frontier"],
			["omlx", "private"],
		] as const) {
			const child = deferred<ExecResult>();
			const harness = createHarness(child.promise, { provider });
			await harness.tool?.execute(
				"delegate",
				{ action: "delegate", task: "add one test" },
				undefined,
				undefined,
				harness.ctx,
			);
			expect(harness.workerArgs?.slice(0, 2)).toEqual(["--route", route]);
			child.resolve({ code: 0, stdout: "done", stderr: "", killed: false });
			await settleBackground();
			await harness.tool?.execute("discard", { action: "discard" }, undefined, undefined, harness.ctx);
		}
	});

	test("worker prompt forbids git mutation and requires verification", () => {
		const prompt = buildWorkerPrompt("add a test", "worker/add-a-test-x");
		expect(prompt).toContain("worker/add-a-test-x");
		expect(prompt).toContain("Do not run git commit");
		expect(prompt).toContain("leave all changes uncommitted");
		expect(prompt).toContain("tests or checks");
	});

	test("review instructions keep adoption and cleanup with the parent", () => {
		const text = reviewInstructions("/tmp/x.worktree", "worker/x", "abc123");
		expect(text).toContain("git -C /tmp/x.worktree diff");
		expect(text).toContain("diff abc123 --");
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
