/**
 * worker — one bounded, worktree-isolated background delegate for Pi
 *
 * The model-callable `worker` tool may start, review, and discard one child
 * worktree. Discarding output requires an explicit adopted/rejected disposition.
 * Delegation returns after setup while the child runs in the background. The
 * child is instructed not to commit, push, install, or merge; the parent reviews,
 * adopts, and verifies useful changes before cleanup.
 */

import { existsSync, lstatSync, realpathSync } from "node:fs";
import { dirname, join, sep } from "node:path";
import type { ExecResult, ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { type Static, Type } from "typebox";
import { loadSettings } from "./lib/settings";
import { buildWorkerPrompt, reviewInstructions, workerSlug } from "./lib/worker-core";

const DEFAULT_TIMEOUT_MS = 900_000;
const MAX_RESULT_CHARS = 6000;
const PROGRESS_INTERVAL_MS = 10_000;
const STATUS_KEY = "worker";

const workerToolSchema = Type.Object({
	action: Type.String({
		enum: ["delegate", "review", "discard"],
		description:
			"delegate starts one independent background implementation task; review inspects progress or the result; discard removes it after adoption or rejection",
	}),
	task: Type.Optional(
		Type.String({ description: "Complete, bounded implementation task. Required for delegate." }),
	),
	disposition: Type.Optional(
		Type.String({
			enum: ["adopted", "rejected"],
			description:
				"Required to discard uncommitted output: adopted means verified in the parent; rejected means intentionally unwanted. Unique commits are preserved.",
		}),
	),
});

export type WorkerToolInput = Static<typeof workerToolSchema>;

type WorkerStatus = "running" | "finished" | "failed";

interface WorkerState {
	root: string;
	dir: string;
	branch: string;
	baseCommit: string;
	task: string;
	finished: boolean;
	status: WorkerStatus;
	startedAt: number;
	finishedAt?: number;
	result?: ExecResult;
	abortController: AbortController;
	progressTimer?: ReturnType<typeof setInterval>;
}

interface WorkerResponse {
	text: string;
	isError?: boolean;
}

function truncate(text: string): string {
	const clean = text.trim();
	if (clean.length <= MAX_RESULT_CHARS) return clean;
	return `${clean.slice(0, MAX_RESULT_CHARS)}\n\n… truncated.`;
}

function timeoutMs(ctx: ExtensionContext): number {
	const value = loadSettings(ctx, "worker").timeoutMs;
	return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : DEFAULT_TIMEOUT_MS;
}

function elapsedMs(state: WorkerState): number {
	return (state.finishedAt ?? Date.now()) - state.startedAt;
}

function elapsedLabel(milliseconds: number): string {
	const seconds = Math.max(0, Math.floor(milliseconds / 1000));
	if (seconds < 60) return `${seconds}s`;
	const minutes = Math.floor(seconds / 60);
	return `${minutes}m ${seconds % 60}s`;
}

function publicState(state: WorkerState | undefined): Record<string, unknown> {
	if (!state) return {};
	return {
		dir: state.dir,
		branch: state.branch,
		baseCommit: state.baseCommit,
		task: state.task,
		finished: state.finished,
		status: state.status,
		startedAt: state.startedAt,
		finishedAt: state.finishedAt,
		exitCode: state.result?.code,
	};
}

function managedPlacementError(root: string): string | undefined {
	if (
		process.env.WORKBENCH_AGENT_AUTHORITY !== "managed" &&
		process.env.WORKBENCH_PI_MODE !== "hosted-managed"
	)
		return;
	const guidance =
		"Start native pi from your host terminal for this checkout, or use a checkout under public code, Desktop, or Downloads.";
	try {
		if (!lstatSync(join(root, ".git")).isDirectory())
			return `Managed workers require an ordinary checkout with a .git directory. ${guidance}`;
		const home = process.env.WORKBENCH_HOST_HOME;
		const parent = dirname(realpathSync(root));
		const allowed =
			home &&
			["code/public", "Desktop", "Downloads"].some((path) => {
				const candidate = join(home, path);
				if (!existsSync(candidate)) return false;
				const shared = realpathSync(candidate);
				return parent === shared || parent.startsWith(shared + sep);
			});
		if (!allowed) return `Worker sibling placement is outside managed write roots. ${guidance}`;
	} catch {
		return `Could not verify managed worker placement in an ordinary checkout. ${guidance}`;
	}
	// This preflight improves diagnostics; the inherited OS sandbox enforces actual writes.
}

export default function workerExtension(pi: ExtensionAPI) {
	let active: WorkerState | undefined;
	let shuttingDown = false;
	pi.registerFlag("worker-child", {
		type: "boolean",
		description: "Mark this session as a bounded worker that cannot delegate another worker",
	});

	function setWorkerStatus(ctx: ExtensionContext, state: WorkerState): void {
		if (!ctx.hasUI || shuttingDown) return;
		const elapsed = elapsedLabel(elapsedMs(state));
		const label =
			state.status === "running"
				? `worker running ${elapsed}`
				: state.status === "finished"
					? `worker done ${elapsed}`
					: `worker failed ${elapsed}`;
		ctx.ui.setStatus(STATUS_KEY, label);
	}

	function stopProgressTimer(state: WorkerState): void {
		if (!state.progressTimer) return;
		clearInterval(state.progressTimer);
		state.progressTimer = undefined;
	}

	function startProgressTimer(ctx: ExtensionContext, state: WorkerState): void {
		setWorkerStatus(ctx, state);
		state.progressTimer = setInterval(() => setWorkerStatus(ctx, state), PROGRESS_INTERVAL_MS);
		state.progressTimer.unref?.();
	}

	async function repoRoot(ctx: ExtensionContext): Promise<string | undefined> {
		const result = await pi.exec("git", ["rev-parse", "--show-toplevel"], {
			cwd: ctx.cwd,
			timeout: 5000,
		});
		const root = result.stdout.trim();
		return result.code === 0 && root ? root : undefined;
	}

	async function reviewWorker(): Promise<WorkerResponse> {
		if (!active) return { text: "No worker this session.", isError: true };
		const status = await inspectGit(["status", "--porcelain", "--untracked-files=all"], active.dir);
		const stat = await inspectGit(["diff", "--stat", active.baseCommit, "--"], active.dir);
		const commits = await inspectGit(["log", "--oneline", `${active.baseCommit}..HEAD`], active.dir);
		const report = active.result
			? active.status === "finished"
				? `Worker report:\n${truncate(active.result.stdout || "(no report)")}`
				: `Worker failed (exit ${active.result.code}).\n${truncate(active.result.stderr || active.result.stdout || "No failure output.")}`
			: undefined;
		return {
			text: [
				`Worker ${active.status} after ${elapsedLabel(elapsedMs(active))}: ${active.task}`,
				stat || status
					? `Changes since ${active.baseCommit}:\n${truncate(stat)}\n\nWorking tree status:\n${truncate(status) || "clean"}`
					: "No file changes yet.",
				commits ? `Unexpected worker commits:\n${truncate(commits)}` : undefined,
				report,
				reviewInstructions(active.dir, active.branch, active.baseCommit),
			]
				.filter(Boolean)
				.join("\n\n"),
			isError: active.status === "failed",
		};
	}

	async function inspectGit(args: string[], cwd: string): Promise<string> {
		const result = await pi.exec("git", args, { cwd, timeout: 10_000 });
		if (result.code !== 0)
			throw new Error(
				`Could not inspect worker (git ${args.join(" ")}):\n${truncate(result.stderr || result.stdout)}`,
			);
		return result.stdout.trim();
	}

	function finishWorker(state: WorkerState, result: ExecResult, ctx: ExtensionContext): void {
		if (active !== state) return;
		state.result = result;
		state.finished = true;
		state.finishedAt = Date.now();
		state.status = result.code === 0 ? "finished" : "failed";
		stopProgressTimer(state);
		setWorkerStatus(ctx, state);
		if (!ctx.hasUI || shuttingDown) return;
		const elapsed = elapsedLabel(elapsedMs(state));
		ctx.ui.notify(
			state.status === "finished"
				? `Worker finished after ${elapsed}. Use worker review to inspect and adopt it.`
				: `Worker failed after ${elapsed} with exit ${result.code}. Use worker review for details.`,
			state.status === "finished" ? "info" : "error",
		);
	}

	async function delegate(task: string, ctx: ExtensionContext): Promise<WorkerResponse> {
		if (pi.getFlag("worker-child") === true)
			return {
				text: "A child worker cannot delegate another worker. Complete the assigned task directly.",
				isError: true,
			};
		// Validate settings before Git creates the branch or worktree.
		const timeout = timeoutMs(ctx);
		const boundedTask = task.trim();
		if (!boundedTask) return { text: "delegate requires a non-empty task.", isError: true };
		if (active) {
			return {
				text: `A worker already exists on ${active.branch}. Review and discard it before delegating another task.`,
				isError: true,
			};
		}
		const root = await repoRoot(ctx);
		if (!root) return { text: "worker needs a git repository.", isError: true };
		const placementError = managedPlacementError(root);
		if (placementError) return { text: placementError, isError: true };
		const parentStatus = await pi.exec("git", ["status", "--porcelain"], {
			cwd: root,
			timeout: 10_000,
		});
		if (parentStatus.code !== 0) {
			return {
				text: `Could not verify that the parent working tree is clean:\n${truncate(parentStatus.stderr || parentStatus.stdout)}`,
				isError: true,
			};
		}
		if (parentStatus.stdout.trim()) {
			return {
				text: [
					"Worker delegation requires a clean parent working tree because the child starts from HEAD.",
					"Commit, stash, or discard tracked and untracked changes before delegating.",
					truncate(parentStatus.stdout),
				].join("\n\n"),
				isError: true,
			};
		}
		const base = await pi.exec("git", ["rev-parse", "--verify", "HEAD"], { cwd: root, timeout: 5000 });
		if (base.code !== 0 || !base.stdout.trim()) {
			return { text: "Could not determine the worker's starting commit.", isError: true };
		}
		const baseCommit = base.stdout.trim();

		const stamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 12);
		const slug = workerSlug(boundedTask, stamp);
		const branch = `worker/${slug}`;
		const dir = join(root, "..", `${slug}.worktree`);
		if (existsSync(dir)) return { text: `Worktree path already exists: ${dir}`, isError: true };

		const add = await pi.exec("git", ["worktree", "add", "-b", branch, dir, baseCommit], {
			cwd: root,
			timeout: 30_000,
		});
		if (add.code !== 0) {
			return {
				text: `git worktree add failed:\n${truncate(add.stderr || add.stdout)}`,
				isError: true,
			};
		}

		const state: WorkerState = {
			root,
			dir,
			branch,
			baseCommit,
			task: boundedTask,
			finished: false,
			status: "running",
			startedAt: Date.now(),
			abortController: new AbortController(),
		};
		active = state;
		startProgressTimer(ctx, state);
		const route = ctx.model?.provider === "omlx" ? "private" : "frontier";
		const modelArgs = ctx.model ? ["--provider", ctx.model.provider, "--model", ctx.model.id] : [];
		void pi
			.exec(
				"pi",
				[
					"--route",
					route,
					...modelArgs,
					"--thinking",
					pi.getThinkingLevel(),
					"--worker-child",
					"-p",
					"--no-session",
					buildWorkerPrompt(boundedTask, branch),
				],
				{
					cwd: dir,
					timeout,
					signal: state.abortController.signal,
				},
			)
			.then((result) => finishWorker(state, result, ctx))
			.catch((error: unknown) => {
				finishWorker(
					state,
					{
						code: 1,
						killed: false,
						stdout: "",
						stderr: error instanceof Error ? error.message : String(error),
					},
					ctx,
				);
			});

		return {
			text: [
				`Worker started in the background on ${branch}.`,
				"Continue independent parent work now. Use worker review later for live diff progress or the final report.",
				reviewInstructions(dir, branch, baseCommit),
			].join("\n\n"),
		};
	}

	async function discard(
		ctx: ExtensionContext,
		force: boolean,
		disposition?: string,
	): Promise<WorkerResponse> {
		if (!active) return { text: "No worker this session.", isError: true };
		if (!active.finished) return { text: "Worker is still running.", isError: true };
		if (disposition !== undefined && disposition !== "adopted" && disposition !== "rejected")
			return { text: "Worker disposition must be adopted or rejected.", isError: true };
		const root = active.root;
		const branchRef = await inspectGit(["symbolic-ref", "--quiet", "HEAD"], active.dir);
		if (branchRef !== `refs/heads/${active.branch}`)
			return {
				text: "Worker branch changed. Preserve the worktree and inspect its branches before cleanup.",
				isError: true,
			};
		const parentHead = await inspectGit(["rev-parse", "--verify", "HEAD"], root);
		const uniqueCommits = await inspectGit(["rev-list", "--count", "HEAD", "--not", parentHead], active.dir);
		if (!/^\d+$/.test(uniqueCommits)) throw new Error("Could not inspect worker commit count.");
		if (Number(uniqueCommits) > 0 && !force) {
			return {
				text: `Worker has ${uniqueCommits} commits not reachable from the parent. Preserve or merge them before cleanup. To deliberately reject these commits, use /worker-done --force.`,
				isError: true,
			};
		}
		const head = await inspectGit(["rev-parse", "--verify", "HEAD"], active.dir);
		if (head !== active.baseCommit && !force && !disposition) {
			return {
				text: "Worker HEAD changed from its starting commit. Review the committed output, then discard with disposition=adopted or disposition=rejected.",
				isError: true,
			};
		}

		const status = await inspectGit(["status", "--porcelain", "--untracked-files=all"], active.dir);
		if (status && !force && !disposition) {
			return {
				text: `Worktree has uncommitted changes. Review first, then discard with disposition=adopted or disposition=rejected.\n${reviewInstructions(active.dir, active.branch, active.baseCommit)}`,
				isError: true,
			};
		}

		const removeArgs = ["worktree", "remove", ...(force || disposition ? ["--force"] : []), active.dir];
		const removed = await pi.exec("git", removeArgs, { cwd: root, timeout: 30_000 });
		if (removed.code !== 0) {
			return {
				text: `git worktree remove failed:\n${truncate(removed.stderr || removed.stdout)}`,
				isError: true,
			};
		}
		const branch = active.branch;
		const dir = active.dir;
		const deleted = await pi.exec("git", ["branch", force ? "-D" : "-d", branch], {
			cwd: root,
			timeout: 10_000,
		});
		stopProgressTimer(active);
		active = undefined;
		if (ctx.hasUI) ctx.ui.setStatus(STATUS_KEY, undefined);
		if (deleted.code !== 0) {
			return {
				text: [
					`Removed ${dir}, but branch deletion failed for ${branch}.`,
					truncate(deleted.stderr || deleted.stdout),
				].join("\n"),
				isError: true,
			};
		}
		const rejectedCommits =
			force && Number(uniqueCommits) > 0
				? ` Explicitly discarded ${uniqueCommits} commit${uniqueCommits === "1" ? "" : "s"} not reachable from the parent.`
				: "";
		return { text: `Removed ${dir} and ${branch}.${rejectedCommits}` };
	}

	async function requireSuccess(response: Promise<WorkerResponse>): Promise<WorkerResponse> {
		const resolved = await response;
		if (resolved.isError) throw new Error(resolved.text);
		return resolved;
	}

	pi.registerTool({
		name: "worker",
		label: "Worker",
		description:
			"Manage one worktree-isolated Pi delegate that runs in the background. Call delegate alone for substantial implementation independent of the parent's next work, continue useful parent work, then call review in a later turn to inspect progress or adopt the result; discard after adoption or rejection. Never delegate work that depends on uncommitted parent files.",
		parameters: workerToolSchema,
		async execute(_toolCallId, input, _signal, _onUpdate, ctx) {
			let response: WorkerResponse;
			if (input.action === "delegate") response = await requireSuccess(delegate(input.task ?? "", ctx));
			else if (input.action === "review") response = await requireSuccess(reviewWorker());
			else response = await requireSuccess(discard(ctx, false, input.disposition));
			return {
				content: [{ type: "text", text: response.text }],
				details: publicState(active),
			};
		},
	});

	pi.registerCommand("worker", {
		description: "Start one child Pi in an isolated worktree: /worker <task>",
		handler: async (args, ctx) => {
			const response = await delegate(args, ctx);
			ctx.ui.notify(response.text, response.isError ? "warning" : "info");
		},
	});

	pi.registerCommand("worker-status", {
		description: "Show the active worker's progress or final report",
		handler: async (_args, ctx) => {
			const response = await reviewWorker();
			ctx.ui.notify(response.text, response.isError ? "warning" : "info");
		},
	});

	pi.registerCommand("worker-done", {
		description: "Remove the worker worktree and branch: /worker-done [adopted|rejected|--force]",
		handler: async (args, ctx) => {
			const argument = args.trim();
			const response = await discard(
				ctx,
				argument === "--force",
				argument && argument !== "--force" ? argument : undefined,
			);
			ctx.ui.notify(response.text, response.isError ? "warning" : "info");
		},
	});

	pi.on("session_shutdown", async (_event, ctx) => {
		shuttingDown = true;
		if (active?.status === "running") active.abortController.abort();
		if (active) stopProgressTimer(active);
		if (ctx.hasUI) ctx.ui.setStatus(STATUS_KEY, undefined);
	});
}
