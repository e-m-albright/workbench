import type { ExtensionAPI, ExtensionContext, SessionEntry, Theme } from "@earendil-works/pi-coding-agent";
import type { Component, TUI } from "@earendil-works/pi-tui";

export interface WorkSummary {
	notes: string[];
	tools: Record<string, number>;
	errors: number;
}

export interface TranscriptTurn {
	prompt: string;
	work: WorkSummary;
	answer?: string;
}

function contentText(content: unknown): string {
	if (typeof content === "string") return content.trim();
	if (!Array.isArray(content)) return "";
	return content
		.filter((block): block is { type: "text"; text: string } => {
			return Boolean(
				block && typeof block === "object" && block.type === "text" && typeof block.text === "string",
			);
		})
		.map((block) => block.text)
		.join("\n")
		.trim();
}

export function parseTranscript(entries: readonly SessionEntry[]): TranscriptTurn[] {
	const turns: TranscriptTurn[] = [];
	let current: TranscriptTurn | undefined;
	let countedToolCalls = new Set<string>();

	for (const entry of entries) {
		if (entry.type !== "message") continue;
		const message = entry.message;

		if (message.role === "user") {
			const prompt = contentText(message.content);
			if (!prompt) continue;
			current = { prompt, work: { notes: [], tools: {}, errors: 0 } };
			turns.push(current);
			countedToolCalls = new Set<string>();
			continue;
		}
		if (!current) continue;

		if (message.role === "assistant") {
			const text = contentText(message.content);
			for (const block of message.content) {
				if (block.type !== "toolCall") continue;
				countedToolCalls.add(block.id);
				current.work.tools[block.name] = (current.work.tools[block.name] ?? 0) + 1;
			}
			if (message.stopReason === "stop" && text) current.answer = text;
			else if (text) current.work.notes.push(text);
			continue;
		}

		if (message.role === "toolResult") {
			if (!countedToolCalls.has(message.toolCallId)) {
				current.work.tools[message.toolName] = (current.work.tools[message.toolName] ?? 0) + 1;
				countedToolCalls.add(message.toolCallId);
			}
			if (message.isError) current.work.errors++;
		}
	}

	return turns;
}

export function formatWorkSummary(work: WorkSummary): string {
	const tools = Object.entries(work.tools);
	const total = tools.reduce((sum, [, count]) => sum + count, 0);
	if (total === 0 && work.notes.length === 0 && work.errors === 0) return "No separate work steps";

	const parts: string[] = [];
	if (total > 0) parts.push(`${total} ${total === 1 ? "tool" : "tools"}`);
	for (const [name, count] of tools.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))) {
		parts.push(`${count} ${name}`);
	}
	if (work.errors > 0) parts.push(`${work.errors} ${work.errors === 1 ? "error" : "errors"}`);
	if (total === 0 && work.notes.length > 0)
		parts.push(`${work.notes.length} progress ${work.notes.length === 1 ? "note" : "notes"}`);
	return parts.join(" · ");
}

export function selectLatestReadableTurn(turns: readonly TranscriptTurn[]): number {
	for (let index = turns.length - 1; index >= 0; index--) {
		if (turns[index]?.answer) return index;
	}
	return turns.length - 1;
}

export function reconcileReaderSelection(
	previousTurns: readonly TranscriptTurn[],
	nextTurns: readonly TranscriptTurn[],
	turnIndex: number,
	followLatest: boolean,
): { turnIndex: number; anchor?: "answer" } {
	if (!followLatest || nextTurns.length === 0)
		return { turnIndex: Math.min(turnIndex, Math.max(0, nextTurns.length - 1)) };
	const previousLatest = previousTurns.at(-1);
	const nextLatest = nextTurns.at(-1);
	return {
		turnIndex: nextTurns.length - 1,
		...(!previousLatest?.answer && nextLatest?.answer ? { anchor: "answer" as const } : {}),
	};
}

export function clampScrollOffset(lineCount: number, _viewportHeight: number, requested: number): number {
	// Reader landmarks should be able to sit at the top even when the remaining
	// content is shorter than the viewport; the viewport pads the rest with blanks.
	return Math.max(0, Math.min(requested, Math.max(0, lineCount - 1)));
}

export type ReaderInput =
	| "close"
	| "previousTurn"
	| "nextTurn"
	| "prompt"
	| "answer"
	| "latest"
	| "work"
	| "up"
	| "down"
	| "pageUp"
	| "pageDown";

type ReaderKey =
	| "escape"
	| "ctrl+c"
	| "["
	| "]"
	| "p"
	| "home"
	| "a"
	| "end"
	| "g"
	| "w"
	| "up"
	| "k"
	| "down"
	| "j"
	| "pageUp"
	| "pageDown";
type KeyMatcher = (data: string, key: ReaderKey) => boolean;

export function classifyReaderInput(data: string, matchesKey: KeyMatcher): ReaderInput | undefined {
	if (matchesKey(data, "escape") || matchesKey(data, "ctrl+c")) return "close";
	if (matchesKey(data, "[")) return "previousTurn";
	if (matchesKey(data, "]")) return "nextTurn";
	if (matchesKey(data, "p") || matchesKey(data, "home")) return "prompt";
	if (matchesKey(data, "a") || matchesKey(data, "end")) return "answer";
	if (matchesKey(data, "g")) return "latest";
	if (matchesKey(data, "w")) return "work";
	if (matchesKey(data, "up") || matchesKey(data, "k")) return "up";
	if (matchesKey(data, "down") || matchesKey(data, "j")) return "down";
	if (matchesKey(data, "pageUp")) return "pageUp";
	if (matchesKey(data, "pageDown")) return "pageDown";
	return undefined;
}

function oneLine(text: string): string {
	return text.replace(/\s+/g, " ").trim();
}

type MarkdownRenderer = (text: string, width: number) => string[];
type Truncator = (text: string, width: number) => string;

class TranscriptReader implements Component {
	private turns: TranscriptTurn[];
	private turnIndex: number;
	private scrollOffset = 0;
	private expandedWork = false;
	private pendingAnchor: "prompt" | "answer" | undefined = "answer";

	constructor(
		initialTurns: TranscriptTurn[],
		private readonly getTurns: () => TranscriptTurn[],
		private followLatest: boolean,
		private readonly tui: TUI,
		private readonly theme: Theme,
		private readonly renderMarkdown: MarkdownRenderer,
		private readonly truncate: Truncator,
		private readonly matchesKey: KeyMatcher,
		private readonly done: () => void,
	) {
		this.turns = initialTurns;
		this.turnIndex = followLatest ? initialTurns.length - 1 : selectLatestReadableTurn(initialTurns);
	}

	invalidate(): void {}

	private buildTurn(width: number): { lines: string[]; answerStart: number; workStart: number } {
		const turn = this.turns[this.turnIndex]!;
		const lines: string[] = [];
		lines.push(this.theme.fg("accent", this.theme.bold("PROMPT")));
		lines.push(...this.renderMarkdown(turn.prompt, width));
		lines.push("");

		const workStart = lines.length;
		const disclosure = this.expandedWork ? "▼" : "▶";
		lines.push(
			this.theme.fg(
				"accent",
				this.theme.bold(this.truncate(`WORK ${disclosure} ${formatWorkSummary(turn.work)}`, width)),
			),
		);
		if (this.expandedWork) {
			for (const note of turn.work.notes) {
				lines.push(this.theme.fg("muted", this.truncate(`• ${oneLine(note)}`, width)));
			}
			if (turn.work.notes.length === 0) {
				lines.push(
					this.theme.fg(
						"dim",
						this.truncate("Full tool detail remains available in the standard Pi transcript.", width),
					),
				);
			}
		}
		lines.push("");

		const answerStart = lines.length;
		lines.push(this.theme.fg("accent", this.theme.bold(turn.answer ? "ANSWER" : "ANSWER · in progress")));
		if (turn.answer) lines.push(...this.renderMarkdown(turn.answer, width));
		else lines.push(this.theme.fg("muted", "No completed final answer yet."));
		return { lines, answerStart, workStart };
	}

	render(width: number): string[] {
		const nextTurns = this.getTurns();
		const selection = reconcileReaderSelection(this.turns, nextTurns, this.turnIndex, this.followLatest);
		this.turns = nextTurns;
		this.turnIndex = selection.turnIndex;
		if (selection.anchor) this.pendingAnchor = selection.anchor;
		const turn = this.turns[this.turnIndex]!;
		const built = this.buildTurn(width);
		if (this.pendingAnchor === "answer") this.scrollOffset = built.answerStart;
		else if (this.pendingAnchor === "prompt") this.scrollOffset = 0;
		this.pendingAnchor = undefined;

		const bodyHeight = Math.max(3, this.tui.terminal.rows - 2);
		this.scrollOffset = clampScrollOffset(built.lines.length, bodyHeight, this.scrollOffset);
		const section =
			this.scrollOffset >= built.answerStart
				? "answer"
				: this.scrollOffset >= built.workStart
					? "work"
					: "prompt";
		const excerpt = oneLine(turn.prompt);
		const headerText = this.truncate(
			`Reader · turn ${this.turnIndex + 1}/${this.turns.length} · ${section} · ${excerpt}`,
			width,
		);
		const header = this.theme.fg("accent", this.theme.bold(headerText));
		const body = built.lines.slice(this.scrollOffset, this.scrollOffset + bodyHeight);
		while (body.length < bodyHeight) body.push("");
		const footer = this.theme.fg(
			"dim",
			this.truncate("[ ] turn  p prompt  a answer  g latest  w work  ↑↓/Pg scroll  esc close", width),
		);
		return [header, ...body, footer];
	}

	handleInput(data: string): void {
		const page = Math.max(3, this.tui.terminal.rows - 5);
		switch (classifyReaderInput(data, this.matchesKey)) {
			case "close":
				this.done();
				break;
			case "previousTurn":
				this.changeTurn(-1);
				break;
			case "nextTurn":
				this.changeTurn(1);
				break;
			case "prompt":
				this.pendingAnchor = "prompt";
				break;
			case "answer":
				this.pendingAnchor = "answer";
				break;
			case "latest":
				this.followLatest = true;
				this.turnIndex = this.turns.length - 1;
				this.pendingAnchor = this.turns.at(-1)?.answer ? "answer" : "prompt";
				break;
			case "work":
				this.expandedWork = !this.expandedWork;
				break;
			case "up":
				this.scrollOffset--;
				break;
			case "down":
				this.scrollOffset++;
				break;
			case "pageUp":
				this.scrollOffset -= page;
				break;
			case "pageDown":
				this.scrollOffset += page;
				break;
		}
		this.tui.requestRender();
	}

	private changeTurn(delta: number): void {
		this.followLatest = false;
		this.turnIndex = Math.max(0, Math.min(this.turns.length - 1, this.turnIndex + delta));
		this.expandedWork = false;
		this.pendingAnchor = this.turns[this.turnIndex]?.answer ? "answer" : "prompt";
	}
}

async function openReader(ctx: ExtensionContext): Promise<void> {
	if (ctx.mode !== "tui") {
		ctx.ui.notify("Transcript Reader is available in Pi’s terminal UI.", "info");
		return;
	}
	const turns = parseTranscript(ctx.sessionManager.getBranch());
	if (turns.length === 0) {
		ctx.ui.notify("No user prompts in this session yet.", "info");
		return;
	}
	const [{ Markdown, matchesKey, truncateToWidth }, { getMarkdownTheme }] = await Promise.all([
		import("@earendil-works/pi-tui"),
		import("@earendil-works/pi-coding-agent"),
	]);
	const markdownTheme = getMarkdownTheme();
	const renderMarkdown: MarkdownRenderer = (text, width) =>
		new Markdown(text, 0, 0, markdownTheme).render(width);
	await ctx.ui.custom<void>(
		(tui, theme, _keybindings, done) => {
			return new TranscriptReader(
				turns,
				() => parseTranscript(ctx.sessionManager.getBranch()),
				!ctx.isIdle(),
				tui,
				theme,
				renderMarkdown,
				truncateToWidth,
				matchesKey,
				() => done(),
			);
		},
		{
			overlay: true,
			overlayOptions: { anchor: "top-left", width: "100%", maxHeight: "100%" },
		},
	);
}

export default function transcriptReader(pi: ExtensionAPI) {
	pi.registerCommand("reader", {
		description: "Open a compact prompt/work/answer transcript navigator",
		handler: async (_args, ctx) => openReader(ctx),
	});

	pi.registerShortcut("ctrl+shift+r", {
		description: "Open Transcript Reader",
		handler: async (ctx) => openReader(ctx),
	});

	pi.on("session_start", (_event, ctx) => {
		ctx.ui.setToolsExpanded(false);
	});

	pi.on("before_agent_start", (event) => ({
		systemPrompt:
			event.systemPrompt +
			"\n\nProgress narration contract: Keep in-progress commentary brief and operational. Do not place substantive conclusions or answers in progress commentary. Put every requested answer and conclusion in the self-contained final response.",
	}));
}
