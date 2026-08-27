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
		"Adopt useful changes in the parent checkout, then verify them there.",
		"Cleanup: call the worker tool with action=discard, or use /worker-done --force.",
	].join("\n");
}
