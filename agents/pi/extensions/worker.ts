/**
 * worker — one bounded, worktree-isolated delegate for Pi
 *
 * The model-callable `worker` tool may delegate, review, and discard one child
 * worktree without a confirmation prompt. The `/worker` commands expose the
 * same lifecycle to the user. The child never commits, pushes, installs, or
 * merges; the parent remains responsible for reviewing, adopting, and verifying
 * useful changes before cleanup.
 */

import { existsSync } from "node:fs";
import { join } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Type, type Static } from "typebox";
import { buildWorkerPrompt, reviewInstructions, workerSlug } from "./lib/worker-core";

const DEFAULT_TIMEOUT_MS = 900_000;
const MAX_RESULT_CHARS = 6000;

const workerToolSchema = Type.Object({
	action: Type.String({
		enum: ["delegate", "review", "discard"],
		description:
			"delegate starts one independent implementation task; review inspects its result; discard removes it after adoption or rejection",
	}),
	task: Type.Optional(
		Type.String({ description: "Complete, bounded implementation task. Required for delegate." }),
	),
});

export type WorkerToolInput = Static<typeof workerToolSchema>;

interface WorkerState {
	dir: string;
	branch: string;
	task: string;
	finished: boolean;
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

export default function workerExtension(pi: ExtensionAPI) {
	let active: WorkerState | undefined;

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
		const state = active.finished ? "finished" : "running";
		const status = await pi.exec("git", ["status", "--porcelain"], {
			cwd: active.dir,
			timeout: 10_000,
		});
		const stat = await pi.exec("git", ["diff", "--stat"], {
			cwd: active.dir,
			timeout: 10_000,
		});
		return {
			text: [
				`Worker ${state}: ${active.task}`,
				status.stdout.trim() ? `Changes:\n${stat.stdout.trim() || status.stdout.trim()}` : "No file changes.",
				reviewInstructions(active.dir, active.branch),
			].join("\n\n"),
		};
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

		active = { dir, branch, task: boundedTask, finished: false };
		const run = await pi.exec("pi", ["-p", "--no-session", buildWorkerPrompt(boundedTask, branch)], {
			cwd: dir,
			timeout: timeoutMs(ctx),
		});
		active.finished = true;
		const review = await reviewWorker();
		if (run.code !== 0) {
			return {
				text: `Worker failed (exit ${run.code}).\n${truncate(run.stderr || run.stdout)}\n\n${review.text}`,
				isError: true,
			};
		}
		return {
			text: [`Worker finished on ${branch}.`, truncate(run.stdout), review.text].join("\n\n"),
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
		await pi.exec("git", ["branch", "-D", active.branch], { cwd: root, timeout: 10_000 });
		const text = `Removed ${active.dir} and ${active.branch}.`;
		active = undefined;
		return { text };
	}

	pi.registerTool({
		name: "worker",
		label: "Worker",
		description:
			"Autonomously manage one worktree-isolated Pi delegate. Use delegate only for substantial independent implementation work that can proceed in parallel. Review and adopt useful changes in the parent checkout, verify them, then discard the worker. Do not use for small tasks or coupled edits. No user confirmation is required.",
		parameters: workerToolSchema,
		async execute(_toolCallId, input, _signal, _onUpdate, ctx) {
			let response: WorkerResponse;
			if (input.action === "delegate") response = await delegate(input.task ?? "", ctx);
			else if (input.action === "review") response = await reviewWorker();
			else response = await discard(ctx, true);
			return {
				content: [{ type: "text", text: response.text }],
				details: active ? { ...active } : {},
				isError: response.isError,
			};
		},
	});

	pi.registerCommand("worker", {
		description: "Delegate one task to a child Pi in an isolated git worktree: /worker <task>",
		handler: async (args, ctx) => {
			const response = await delegate(args, ctx);
			ctx.ui.notify(response.text, response.isError ? "warning" : "info");
		},
	});

	pi.registerCommand("worker-status", {
		description: "Show the active or last worker delegate",
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
}
