import { basename } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

const FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
const MAX_THREAD_LENGTH = 48;
const MAX_THREAD_WORDS = 7;
const MAX_PHASE_LENGTH = 72;
const WIDGET_KEY = "activity-progress";

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
		const clipped = title
			.slice(0, MAX_THREAD_LENGTH - 1)
			.replace(/\s+\S*$/, "")
			.trimEnd();
		title = `${clipped || title.slice(0, MAX_THREAD_LENGTH - 1).trimEnd()}…`;
	}
	return title || "new session";
}

export function normalizePhase(value: string): string {
	const phase = value
		.replace(/[\r\n\t]+/g, " ")
		.replace(/\s+/g, " ")
		.trim();
	if (!phase) return "Working";
	if (phase.length <= MAX_PHASE_LENGTH) return phase;
	return `${phase.slice(0, MAX_PHASE_LENGTH - 1).trimEnd()}…`;
}

export function formatElapsed(elapsedMs: number): string {
	const totalMinutes = Math.max(0, Math.floor(elapsedMs / 60_000));
	if (totalMinutes < 60) return `${totalMinutes}m`;
	const totalHours = Math.floor(totalMinutes / 60);
	if (totalHours < 24) {
		return `${totalHours}h ${String(totalMinutes % 60).padStart(2, "0")}m`;
	}
	const days = Math.floor(totalHours / 24);
	return `${days}d ${String(totalHours % 24).padStart(2, "0")}h`;
}

export function formatActivityLine(phase: string, elapsed: string, width: number, indicator = "π"): string {
	if (width <= 0) return "";
	const right = `total ${elapsed}`;
	const rightWidth = visibleWidth(right);
	const availableLeft = width - rightWidth - 1;
	if (availableLeft <= 0) return truncateToWidth(right, width, "");

	const left = truncateToWidth(`${indicator} ${normalizePhase(phase)}`, availableLeft, "…");
	const spacing = Math.max(1, width - visibleWidth(left) - rightWidth);
	return truncateToWidth(`${left}${" ".repeat(spacing)}${right}`, width, "");
}

export function formatActivityTitle(
	project: string,
	thread: string | undefined,
	indicator = "π",
	activity?: string,
): string {
	const context = thread ? `${project} | ${thread}` : project;
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

// ctx.sessionManager is typed ReadonlySessionManager; appendSessionInfo exists only
// on the concrete SessionManager Pi currently passes through. Guard the call so a
// future Pi that enforces the read-only wrapper degrades to an unnamed session
// instead of crashing the extension.
function nameSession(ctx: ExtensionContext, name: string): void {
	const manager = ctx.sessionManager as unknown as { appendSessionInfo?: (name: string) => void };
	manager.appendSessionInfo?.(name);
}

export default function activityTitle(pi: ExtensionAPI) {
	let timer: ReturnType<typeof setInterval> | undefined;
	let frameIndex = 0;
	let project = basename(process.cwd()) || "project";
	let thread: string | undefined;
	let basePhase = "Working";
	let runStartedAt: number | undefined;
	let requestRender: (() => void) | undefined;
	const activeTools = new Map<string, string>();

	function phase(): string {
		const tool = [...activeTools.values()].at(-1);
		return tool ? normalizePhase(`Using ${tool}`) : basePhase;
	}

	function elapsed(now = Date.now()): string {
		return formatElapsed(runStartedAt === undefined ? 0 : now - runStartedAt);
	}

	function renderTitle(ctx: ExtensionContext, indicator = "π"): void {
		ctx.ui.setTitle(formatActivityTitle(project, thread, indicator, timer ? phase() : undefined));
	}

	function refresh(ctx: ExtensionContext): void {
		const indicator = FRAMES[frameIndex % FRAMES.length] ?? "π";
		renderTitle(ctx, indicator);
		requestRender?.();
	}

	function stop(ctx: ExtensionContext): void {
		if (timer) clearInterval(timer);
		timer = undefined;
		frameIndex = 0;
		runStartedAt = undefined;
		requestRender = undefined;
		activeTools.clear();
		ctx.ui.setWidget(WIDGET_KEY, undefined);
		ctx.ui.setWorkingVisible(true);
		renderTitle(ctx);
	}

	function start(ctx: ExtensionContext): void {
		if (timer) clearInterval(timer);
		ctx.ui.setWorkingVisible(false);
		ctx.ui.setWidget(
			WIDGET_KEY,
			(tui, theme) => {
				requestRender = () => tui.requestRender();
				return {
					render(width: number): string[] {
						const indicator = FRAMES[frameIndex % FRAMES.length] ?? "π";
						return [theme.fg("muted", formatActivityLine(phase(), elapsed(), width, indicator))];
					},
					invalidate() {},
					dispose() {
						requestRender = undefined;
					},
				};
			},
			{ placement: "aboveEditor" },
		);
		timer = setInterval(() => {
			frameIndex = (frameIndex + 1) % FRAMES.length;
			refresh(ctx);
		}, 100);
		refresh(ctx);
	}

	pi.on("session_start", async (_event, ctx) => {
		thread = ctx.sessionManager.getSessionName();
		if (!thread) {
			const prompt = firstUserPrompt(ctx);
			if (prompt) {
				thread = deriveThreadTitle(prompt);
				nameSession(ctx, thread);
			}
		}
		const root = await pi.exec("git", ["rev-parse", "--show-toplevel"], { cwd: ctx.cwd, timeout: 1000 });
		if (root.code === 0 && root.stdout.trim()) project = basename(root.stdout.trim());
		else project = basename(ctx.cwd) || "project";
		renderTitle(ctx);
	});

	pi.on("session_info_changed", async (event, ctx) => {
		thread = event.name;
		renderTitle(ctx);
	});

	pi.registerCommand("rename", {
		description: "Rename this session and update the live title immediately",
		handler: async (args, ctx) => {
			const name = args.trim();
			if (!name) {
				ctx.ui.notify("Usage: /rename <name>", "warning");
				return;
			}
			pi.setSessionName(name);
			thread = pi.getSessionName() ?? name;
			renderTitle(ctx, timer ? (FRAMES[frameIndex % FRAMES.length] ?? "π") : "π");
		},
	});

	pi.on("before_agent_start", async (event, ctx) => {
		if (!ctx.sessionManager.getSessionName()) {
			thread = deriveThreadTitle(event.prompt);
			nameSession(ctx, thread);
		} else {
			thread = ctx.sessionManager.getSessionName();
		}
		basePhase = normalizePhase(`Working on ${deriveThreadTitle(event.prompt)}`);
		runStartedAt = Date.now();
		renderTitle(ctx);
	});

	pi.on("agent_start", async (_event, ctx) => {
		start(ctx);
	});

	pi.on("tool_execution_start", async (event, ctx) => {
		activeTools.set(event.toolCallId, event.toolName);
		refresh(ctx);
	});

	pi.on("tool_execution_end", async (event, ctx) => {
		activeTools.delete(event.toolCallId);
		refresh(ctx);
	});

	pi.on("agent_settled", async (_event, ctx) => {
		stop(ctx);
	});

	pi.on("session_shutdown", async (_event, ctx) => {
		stop(ctx);
	});
}
