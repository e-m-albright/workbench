import { basename } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
const MAX_THREAD_LENGTH = 48;
const MAX_THREAD_WORDS = 7;

export function deriveThreadTitle(prompt: string): string {
	const plain = prompt
		.replace(/https?:\/\/\S+/g, "")
		.replace(/[`*_#>\[\](){}]/g, " ")
		.replace(/[\r\n\t]+/g, " ")
		.replace(/\s+/g, " ")
		.trim()
		.replace(/^(?:please\s+)?(?:can|could|would|will)\s+you\s+(?:please\s+)?/i, "")
		.replace(
			/^(?:please\s+)?(?:i\s+(?:would\s+)?like\s+(?:you\s+)?to|i\s+want\s+(?:you\s+)?to|look\s+for)\s+/i,
			"",
		);
	const clause = plain.split(/[.!?;]/, 1)[0]?.trim() ?? "";
	const words = clause.split(/\s+/).filter(Boolean).slice(0, MAX_THREAD_WORDS);
	let title = words.join(" ").replace(/^[,\s]+|[,\s]+$/g, "");
	if (title.length > MAX_THREAD_LENGTH) {
		const clipped = title.slice(0, MAX_THREAD_LENGTH - 1).replace(/\s+\S*$/, "").trimEnd();
		title = `${clipped || title.slice(0, MAX_THREAD_LENGTH - 1).trimEnd()}…`;
	}
	return title || "new session";
}

export function formatActivityTitle(
	project: string,
	thread: string | undefined,
	indicator = "π",
	activity?: string,
): string {
	const context = thread ? `${project} / ${thread}` : project;
	return activity ? `${indicator} ${context} · ${activity}` : `${indicator} ${context}`;
}

function firstUserPrompt(ctx: ExtensionContext): string | undefined {
	for (const entry of ctx.sessionManager.getEntries()) {
		if (entry.type !== "message" || entry.message.role !== "user") continue;
		const content = entry.message.content;
		if (typeof content === "string") return content;
		const text = content
			.filter((block): block is { type: "text"; text: string } => block.type === "text")
			.map((block) => block.text)
			.join(" ");
		if (text) return text;
	}
	return undefined;
}

export default function activityTitle(pi: ExtensionAPI) {
	let timer: ReturnType<typeof setInterval> | undefined;
	let frameIndex = 0;
	let project = basename(process.cwd()) || "project";
	let thread: string | undefined;
	const activeTools = new Map<string, string>();

	function currentActivity(): string | undefined {
		return [...activeTools.values()].at(-1);
	}

	function render(ctx: ExtensionContext, indicator = "π"): void {
		ctx.ui.setTitle(formatActivityTitle(project, thread, indicator, currentActivity()));
	}

	function stop(ctx: ExtensionContext): void {
		if (timer) clearInterval(timer);
		timer = undefined;
		frameIndex = 0;
		activeTools.clear();
		render(ctx);
	}

	function start(ctx: ExtensionContext): void {
		if (timer) clearInterval(timer);
		timer = setInterval(() => {
			const frame = FRAMES[frameIndex % FRAMES.length];
			frameIndex++;
			render(ctx, frame);
		}, 100);
		render(ctx, FRAMES[0]);
	}

	pi.on("session_start", async (_event, ctx) => {
		thread = ctx.sessionManager.getSessionName();
		if (!thread) {
			const prompt = firstUserPrompt(ctx);
			if (prompt) {
				thread = deriveThreadTitle(prompt);
				ctx.sessionManager.appendSessionInfo(thread);
			}
		}
		const root = await pi.exec("git", ["rev-parse", "--show-toplevel"], { cwd: ctx.cwd, timeout: 1000 });
		if (root.code === 0 && root.stdout.trim()) project = basename(root.stdout.trim());
		else project = basename(ctx.cwd) || "project";
		render(ctx);
	});

	pi.on("before_agent_start", async (event, ctx) => {
		if (!ctx.sessionManager.getSessionName()) {
			thread = deriveThreadTitle(event.prompt);
			ctx.sessionManager.appendSessionInfo(thread);
		} else {
			thread = ctx.sessionManager.getSessionName();
		}
		render(ctx);
	});

	pi.on("agent_start", async (_event, ctx) => {
		start(ctx);
	});

	pi.on("tool_execution_start", async (event, ctx) => {
		activeTools.set(event.toolCallId, event.toolName);
		render(ctx, FRAMES[frameIndex % FRAMES.length]);
	});

	pi.on("tool_execution_end", async (event, ctx) => {
		activeTools.delete(event.toolCallId);
		render(ctx, FRAMES[frameIndex % FRAMES.length]);
	});

	pi.on("agent_settled", async (_event, ctx) => {
		stop(ctx);
	});

	pi.on("session_shutdown", async (_event, ctx) => {
		stop(ctx);
	});
}
