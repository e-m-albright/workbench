import { randomUUID } from "node:crypto";
import {
	appendFileSync,
	existsSync,
	mkdirSync,
	readdirSync,
	readFileSync,
	rmSync,
	statSync,
} from "node:fs";
import { basename, join, relative, resolve } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { getAgentDir } from "@earendil-works/pi-coding-agent";

interface DiscoveryConfig {
	enabledByDefault?: boolean;
	retentionDays?: number;
	maxBytesPerDay?: number;
}

interface SettingsFile {
	discoveryTelemetry?: DiscoveryConfig;
}

interface LogEvent {
	ts: string;
	run: string;
	repo: string;
	event: string;
	[key: string]: unknown;
}

const DEFAULTS: Required<DiscoveryConfig> = {
	enabledByDefault: true,
	retentionDays: 7,
	maxBytesPerDay: 5_000_000,
};

const runId = randomUUID();
const stateRoot =
	process.env.XDG_STATE_HOME ?? join(process.env.HOME ?? process.cwd(), ".local", "state");
const logDir = join(stateRoot, "workbench", "pi-discovery");

function config(): Required<DiscoveryConfig> {
	try {
		const settings = JSON.parse(readFileSync(join(getAgentDir(), "settings.json"), "utf8")) as SettingsFile;
		return { ...DEFAULTS, ...(settings.discoveryTelemetry ?? {}) };
	} catch {
		return DEFAULTS;
	}
}

function today(): string {
	return new Date().toISOString().slice(0, 10);
}

function logPath(): string {
	return join(logDir, `${today()}.jsonl`);
}

function repoName(ctx: ExtensionContext): string {
	return basename(resolve(ctx.cwd)) || "unknown";
}

function safePath(ctx: ExtensionContext, value: unknown): string | undefined {
	if (typeof value !== "string" || !value) return undefined;
	const absolute = resolve(ctx.cwd, value.replace(/^~(?=\/)/, process.env.HOME ?? "~"));
	const rel = relative(resolve(ctx.cwd), absolute);
	if (rel === "" || (!rel.startsWith("..") && !rel.startsWith("/"))) return rel || ".";
	return `<external>/${basename(absolute)}`;
}

function cleanOldLogs(retentionDays: number): void {
	if (!existsSync(logDir)) return;
	const cutoff = Date.now() - retentionDays * 86_400_000;
	for (const name of readdirSync(logDir)) {
		if (!name.endsWith(".jsonl")) continue;
		const path = join(logDir, name);
		if (statSync(path).mtimeMs < cutoff) rmSync(path, { force: true });
	}
}

function append(ctx: ExtensionContext, payload: Omit<LogEvent, "ts" | "run" | "repo">): void {
	if (!ctx.isProjectTrusted()) return;
	const cfg = config();
	mkdirSync(logDir, { recursive: true });
	const path = logPath();
	if (existsSync(path) && statSync(path).size >= cfg.maxBytesPerDay) return;
	const event: LogEvent = {
		ts: new Date().toISOString(),
		run: runId,
		repo: repoName(ctx),
		...payload,
	};
	appendFileSync(path, `${JSON.stringify(event)}\n`, { encoding: "utf8", mode: 0o600 });
}

function commandClass(command: string): string {
	const first = command.trim().split(/\s+/)[0] ?? "unknown";
	if (["rg", "grep", "find", "fd", "ls"].includes(first)) return "search";
	if (["pytest", "vitest", "jest", "cargo", "go", "just"].includes(first)) return "verify";
	if (first === "git") return "git";
	if (["tsc", "pyright", "ruff", "eslint", "mypy"].includes(first)) return "analyze";
	return "other";
}

function toolMetadata(ctx: ExtensionContext, toolName: string, input: unknown): Record<string, unknown> {
	const record = input && typeof input === "object" ? (input as Record<string, unknown>) : {};
	if (toolName === "read") {
		return {
			path: safePath(ctx, record.path),
			offset: typeof record.offset === "number" ? record.offset : undefined,
			limit: typeof record.limit === "number" ? record.limit : undefined,
		};
	}
	if (toolName === "edit") {
		return {
			path: safePath(ctx, record.path),
			edit_count: Array.isArray(record.edits) ? record.edits.length : undefined,
		};
	}
	if (toolName === "write") {
		return {
			path: safePath(ctx, record.path),
			bytes: typeof record.content === "string" ? Buffer.byteLength(record.content) : undefined,
		};
	}
	if (toolName === "bash") {
		return {
			class: commandClass(typeof record.command === "string" ? record.command : ""),
		};
	}
	return {};
}

function resultText(value: unknown): string {
	if (typeof value === "string") return value;
	if (!value || typeof value !== "object") return "";
	const record = value as Record<string, unknown>;
	if (typeof record.text === "string") return record.text;
	if (typeof record.output === "string") return record.output;
	if (Array.isArray(record.content)) {
		return record.content
			.map((item) => {
				if (typeof item === "string") return item;
				if (item && typeof item === "object" && typeof (item as Record<string, unknown>).text === "string") {
					return String((item as Record<string, unknown>).text);
				}
				return "";
			})
			.join("\n");
	}
	return "";
}

function readEvents(days: number): LogEvent[] {
	if (!existsSync(logDir)) return [];
	const cutoff = Date.now() - days * 86_400_000;
	const events: LogEvent[] = [];
	for (const name of readdirSync(logDir).filter((item) => item.endsWith(".jsonl")).sort()) {
		for (const line of readFileSync(join(logDir, name), "utf8").split("\n")) {
			if (!line) continue;
			try {
				const event = JSON.parse(line) as LogEvent;
				if (Date.parse(event.ts) >= cutoff) events.push(event);
			} catch {
				// A partial final line after interruption is ignored.
			}
		}
	}
	return events;
}

function report(events: LogEvent[]): string {
	if (events.length === 0) return "No discovery telemetry recorded yet.";
	const calls = events.filter((event) => event.event === "tool_call");
	const ends = events.filter((event) => event.event === "tool_end");
	const reads = calls.filter((event) => event.tool === "read");
	const readCounts = new Map<string, number>();
	for (const event of reads) {
		const path = String(event.path ?? "unknown");
		readCounts.set(path, (readCounts.get(path) ?? 0) + 1);
	}
	const repeatedReads = [...readCounts.values()].reduce((total, count) => total + Math.max(0, count - 1), 0);
	const failures = ends.filter((event) => event.success === false).length;
	const zeroSearches = ends.filter((event) => event.class === "search" && event.result_lines === 0).length;
	const turns = events.filter((event) => event.event === "turn_end");
	const maxContext = Math.max(0, ...turns.map((event) => Number(event.context_tokens ?? 0)));
	const repos = new Set(events.map((event) => event.repo));

	return [
		`Discovery telemetry (${repos.size} repo${repos.size === 1 ? "" : "s"}, ${events.length} events)`,
		`  Tool calls: ${calls.length}`,
		`  Reads: ${reads.length} (${repeatedReads} repeated reads of an already-opened path)`,
		`  Failed tools: ${failures}`,
		`  Zero-result searches: ${zeroSearches}`,
		`  Peak context: ${Math.round(maxContext / 1000)}k tokens`,
		`  Raw logs: ${logDir}`,
	].join("\n");
}

export default function discoveryTelemetry(pi: ExtensionAPI) {
	let enabledOverride: boolean | undefined;
	const pending = new Map<string, { started: number; class?: string }[]>();

	function enabled(): boolean {
		return enabledOverride ?? config().enabledByDefault;
	}

	pi.registerCommand("discovery", {
		description: "Discovery telemetry: status, on, off, report, or clear",
		handler: async (args, ctx) => {
			const action = args.trim().toLowerCase() || "status";
			if (action === "on") enabledOverride = true;
			else if (action === "off") enabledOverride = false;
			else if (action === "clear") {
				rmSync(logDir, { recursive: true, force: true });
				ctx.ui.notify("Discovery telemetry logs cleared.", "info");
				return;
			} else if (action === "report") {
				ctx.ui.notify(report(readEvents(config().retentionDays)), "info");
				return;
			} else if (action !== "status") {
				ctx.ui.notify("Usage: /discovery status|on|off|report|clear", "warning");
				return;
			}
			ctx.ui.notify(
				`Discovery telemetry ${enabled() ? "ON" : "OFF"}\nLocal metadata only: ${logDir}`,
				"info",
			);
		},
	});

	pi.on("session_start", async (_event, ctx) => {
		cleanOldLogs(config().retentionDays);
		if (enabled()) append(ctx, { event: "session_start" });
	});

	pi.on("tool_call", async (event, ctx) => {
		if (!enabled()) return undefined;
		const toolName = event.toolName;
		const metadata = toolMetadata(ctx, toolName, event.input);
		const queue = pending.get(toolName) ?? [];
		queue.push({ started: Date.now(), class: typeof metadata.class === "string" ? metadata.class : undefined });
		pending.set(toolName, queue);
		append(ctx, { event: "tool_call", tool: toolName, ...metadata });
		return undefined;
	});

	pi.on("tool_execution_end", async (event, ctx) => {
		if (!enabled()) return;
		const raw = event as unknown as Record<string, unknown>;
		const toolName = String(raw.toolName ?? raw.name ?? "unknown");
		const queue = pending.get(toolName) ?? [];
		const call = queue.shift();
		if (queue.length > 0) pending.set(toolName, queue);
		else pending.delete(toolName);
		const output = resultText(raw.result ?? raw.output);
		const success = !(raw.isError === true || raw.error);
		append(ctx, {
			event: "tool_end",
			tool: toolName,
			class: call?.class,
			success,
			duration_ms: call ? Date.now() - call.started : undefined,
			result_chars: output.length,
			result_lines: output ? output.split("\n").filter(Boolean).length : 0,
		});
	});

	pi.on("turn_end", async (_event, ctx) => {
		if (!enabled()) return;
		const usage = ctx.getContextUsage();
		append(ctx, {
			event: "turn_end",
			context_tokens: usage?.tokens,
			context_percent: usage?.percent,
		});
	});

	pi.on("session_shutdown", async (_event, ctx) => {
		if (enabled()) append(ctx, { event: "session_shutdown" });
	});
}
