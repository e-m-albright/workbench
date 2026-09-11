/**
 * worker — one bounded, worktree-isolated background delegate for Pi
 *
 * The model-callable `worker` tool may start, review, and discard one child
 * worktree without a confirmation prompt. Delegation returns after setup while
 * the child runs in the background. The child never commits, pushes, installs,
 * or merges; the parent remains responsible for reviewing, adopting, and
 * verifying useful changes before cleanup.
 */

import { existsSync } from "node:fs";
import { join } from "node:path";
import type { ExecResult, ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Type, type Static } from "typebox";
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
});

export type WorkerToolInput = Static<typeof workerToolSchema>;

type WorkerStatus = "running" | "finished" | "failed";

interface WorkerState {
	dir: string;
	branch: string;
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
	// Unofficial settings surface (no public getSettings on ExtensionContext yet).
	const settings =
		(
			ctx as unknown as { settingsManager?: { getSettings(): Record<string, any> } }
		).settingsManager?.getSettings() ?? {};
	const value = Number(settings.worker?.timeoutMs);
	return Number.isFinite(value) && value > 0 ? value : DEFAULT_TIMEOUT_MS;
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
		task: state.task,
		finished: state.finished,
		status: state.status,
		startedAt: state.startedAt,
		finishedAt: state.finishedAt,
		exitCode: state.result?.code,
	};
}

export default function workerExtension(pi: ExtensionAPI) {
	let active: WorkerState | undefined;
	let shuttingDown = false;

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
		const status = await pi.exec("git", ["status", "--porcelain"], {
			cwd: active.dir,
			timeout: 10_000,
		});
		const stat = await pi.exec("git", ["diff", "--stat"], {
			cwd: active.dir,
			timeout: 10_000,
		});
		const report = active.result
			? active.status === "finished"
				? `Worker report:\n${truncate(active.result.stdout || "(no report)")}`
				: `Worker failed (exit ${active.result.code}).\n${truncate(active.result.stderr || active.result.stdout || "No failure output.")}`
			: undefined;
		return {
			text: [
				`Worker ${active.status} after ${elapsedLabel(elapsedMs(active))}: ${active.task}`,
				status.stdout.trim()
					? `Changes:\n${stat.stdout.trim() || status.stdout.trim()}`
					: "No file changes yet.",
				report,
				reviewInstructions(active.dir, active.branch),
			]
				.filter(Boolean)
				.join("\n\n"),
			isError: active.status === "failed",
		};
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

		const stamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 12);
		const slug = workerSlug(boundedTask, stamp);
		const branch = `worker/${slug}`;
		const dir = join(root, "..", `${slug}.worktree`);
		if (existsSync(dir)) return { text: `Worktree path already exists: ${dir}`, isError: true };

		const add = await pi.exec("git", ["worktree", "add", "-b", branch, dir, "HEAD"], {
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
			dir,
			branch,
			task: boundedTask,
			finished: false,
			status: "running",
			startedAt: Date.now(),
			abortController: new AbortController(),
		};
		active = state;
		startProgressTimer(ctx, state);
		void pi
			.exec("pi", ["-p", "--no-session", buildWorkerPrompt(boundedTask, branch)], {
				cwd: dir,
				timeout: timeoutMs(ctx),
				signal: state.abortController.signal,
			})
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
				reviewInstructions(dir, branch),
			].join("\n\n"),
		};
	}

	async function discard(ctx: ExtensionContext, force: boolean): Promise<WorkerResponse> {
		if (!active) return { text: "No worker this session.", isError: true };
		if (!active.finished) return { text: "Worker is still running.", isError: true };
		const root = await repoRoot(ctx);
		if (!root) return { text: "worker needs a git repository.", isError: true };

		const status = await pi.exec("git", ["status", "--porcelain"], {
			cwd: active.dir,
			timeout: 10_000,
		});
		if (status.code === 0 && status.stdout.trim() && !force) {
			return {
				text: `Worktree has uncommitted changes. Review first, then force cleanup.\n${reviewInstructions(active.dir, active.branch)}`,
				isError: true,
			};
		}

		const removeArgs = ["worktree", "remove", ...(force ? ["--force"] : []), active.dir];
		const removed = await pi.exec("git", removeArgs, { cwd: root, timeout: 30_000 });
		if (removed.code !== 0) {
			return {
				text: `git worktree remove failed:\n${truncate(removed.stderr || removed.stdout)}`,
				isError: true,
			};
		}
		const branch = active.branch;
		const dir = active.dir;
		const deleted = await pi.exec("git", ["branch", "-D", branch], { cwd: root, timeout: 10_000 });
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
		return { text: `Removed ${dir} and ${branch}.` };
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
			else response = await requireSuccess(discard(ctx, true));
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
		description: "Remove the worker worktree and branch: /worker-done [--force]",
		handler: async (args, ctx) => {
			const response = await discard(ctx, args.trim() === "--force");
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
