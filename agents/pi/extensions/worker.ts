/**
 * worker — one bounded, worktree-isolated delegate for Pi
 *
 * /worker <task> runs a single child Pi in print mode inside a fresh git
 * worktree, so the delegate can mutate files without touching the parent
 * checkout. The child is instructed to leave its changes uncommitted; the
 * parent (you) reviews the diff and decides what merges. This is deliberately
 * the smallest useful slice of "subagents": one worker at a time, no roster,
 * no autonomous merge or push, parent-owned verification.
 *
 * Commands:
 *   /worker <task>        start the delegate (blocks until it finishes)
 *   /worker-status        show the active or last worker and review commands
 *   /worker-done [--force] remove the worker's worktree and branch
 *
 * Optional settings (~/.pi/agent/settings.json):
 *   { "worker": { "timeoutMs": 900000 } }
 */

import { existsSync } from "node:fs";
import { join } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const DEFAULT_TIMEOUT_MS = 900_000;
const MAX_NOTIFY_CHARS = 6000;

export function workerSlug(task: string, stamp: string): string {
  const words = task
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 4)
    .join("-");
  return `${words || "task"}-${stamp}`;
}

export function buildWorkerPrompt(task: string, branch: string): string {
  return `You are a delegated worker agent in an isolated git worktree on branch ${branch}.

Rules:
- Work only inside this directory.
- Do not run git commit, merge, push, or any other git mutation; leave all changes uncommitted for the parent agent to review.
- Do not install or remove dependencies, deploy, or touch files outside this worktree.
- Run the project's relevant tests or checks to verify your changes and include the output summary.

Task:
${task}

Finish with a concise report: what changed (file list), how it was verified, and anything left open.`;
}

export function reviewInstructions(dir: string, branch: string): string {
  return [
    `Worktree: ${dir}`,
    `Branch: ${branch}`,
    `Review:  git -C ${dir} diff`,
    `Adopt:   git -C ${dir} diff | git apply   (from the main checkout)`,
    `Discard: /worker-done --force`,
  ].join("\n");
}

interface WorkerState {
  dir: string;
  branch: string;
  task: string;
  finished: boolean;
}

function truncate(text: string): string {
  const clean = text.trim();
  if (clean.length <= MAX_NOTIFY_CHARS) return clean;
  return `${clean.slice(0, MAX_NOTIFY_CHARS)}\n\n… truncated.`;
}

function timeoutMs(ctx: ExtensionContext): number {
  const settings = (ctx as any).settingsManager?.getSettings?.() ?? {};
  const value = Number(settings.worker?.timeoutMs);
  return Number.isFinite(value) && value > 0 ? value : DEFAULT_TIMEOUT_MS;
}

export default function workerExtension(pi: ExtensionAPI) {
  let active: WorkerState | undefined;

  async function repoRoot(ctx: ExtensionContext): Promise<string | undefined> {
    const result = await pi.exec("git", ["rev-parse", "--show-toplevel"], { cwd: ctx.cwd, timeout: 5000 });
    const root = result.stdout.trim();
    return result.code === 0 && root ? root : undefined;
  }

  pi.registerCommand("worker", {
    description: "Delegate one task to a child Pi in an isolated git worktree: /worker <task>",
    handler: async (args, ctx) => {
      const task = args.trim();
      if (!task) {
        ctx.ui.notify("Usage: /worker <task>", "warning");
        return;
      }
      if (active && !active.finished) {
        ctx.ui.notify(`A worker is already running on ${active.branch}. One worker at a time.`, "warning");
        return;
      }
      const root = await repoRoot(ctx);
      if (!root) {
        ctx.ui.notify("/worker needs a git repository.", "warning");
        return;
      }

      const stamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 12);
      const slug = workerSlug(task, stamp);
      const branch = `worker/${slug}`;
      const dir = join(root, "..", `${slug}.worktree`);
      if (existsSync(dir)) {
        ctx.ui.notify(`Worktree path already exists: ${dir}`, "warning");
        return;
      }

      const add = await pi.exec("git", ["worktree", "add", "-b", branch, dir, "HEAD"], {
        cwd: root,
        timeout: 30_000,
      });
      if (add.code !== 0) {
        ctx.ui.notify(`git worktree add failed:\n${truncate(add.stderr || add.stdout)}`, "warning");
        return;
      }

      active = { dir, branch, task, finished: false };
      ctx.ui.notify(`Worker started on ${branch}\n${dir}`, "info");

      const run = await pi.exec("pi", ["-p", "--no-session", buildWorkerPrompt(task, branch)], {
        cwd: dir,
        timeout: timeoutMs(ctx),
      });
      active.finished = true;

      const status = await pi.exec("git", ["status", "--porcelain"], { cwd: dir, timeout: 10_000 });
      const stat = await pi.exec("git", ["diff", "--stat"], { cwd: dir, timeout: 10_000 });
      const changed = status.stdout.trim();

      if (run.code !== 0) {
        ctx.ui.notify(
          `Worker failed (exit ${run.code}).\n${truncate(run.stderr || run.stdout)}\n\n${reviewInstructions(dir, branch)}`,
          "warning",
        );
        return;
      }
      ctx.ui.notify(
        [
          `Worker finished on ${branch}.`,
          "",
          truncate(run.stdout),
          "",
          changed ? `Changes:\n${stat.stdout.trim() || changed}` : "No file changes.",
          "",
          reviewInstructions(dir, branch),
        ].join("\n"),
        "info",
      );
    },
  });

  pi.registerCommand("worker-status", {
    description: "Show the active or last /worker delegate",
    handler: async (_args, ctx) => {
      if (!active) {
        ctx.ui.notify("No worker this session.", "info");
        return;
      }
      const state = active.finished ? "finished" : "running";
      ctx.ui.notify(
        `Worker ${state}: ${active.task}\n${reviewInstructions(active.dir, active.branch)}`,
        "info",
      );
    },
  });

  pi.registerCommand("worker-done", {
    description: "Remove the worker worktree and branch: /worker-done [--force]",
    handler: async (args, ctx) => {
      if (!active) {
        ctx.ui.notify("No worker this session.", "info");
        return;
      }
      if (!active.finished) {
        ctx.ui.notify("Worker is still running.", "warning");
        return;
      }
      const force = args.trim() === "--force";
      const root = await repoRoot(ctx);
      if (!root) return;

      const status = await pi.exec("git", ["status", "--porcelain"], { cwd: active.dir, timeout: 10_000 });
      if (status.code === 0 && status.stdout.trim() && !force) {
        ctx.ui.notify(
          `Worktree has uncommitted changes. Review first, then /worker-done --force to discard.\n${reviewInstructions(active.dir, active.branch)}`,
          "warning",
        );
        return;
      }

      const removeArgs = ["worktree", "remove", ...(force ? ["--force"] : []), active.dir];
      const removed = await pi.exec("git", removeArgs, { cwd: root, timeout: 30_000 });
      if (removed.code !== 0) {
        ctx.ui.notify(`git worktree remove failed:\n${truncate(removed.stderr || removed.stdout)}`, "warning");
        return;
      }
      await pi.exec("git", ["branch", "-D", active.branch], { cwd: root, timeout: 10_000 });
      ctx.ui.notify(`Removed ${active.dir} and ${active.branch}.`, "info");
      active = undefined;
    },
  });
}
