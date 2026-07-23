import { randomUUID } from "node:crypto";
import {
	appendFileSync,
	chmodSync,
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

function fileMtime(ctx: ExtensionContext, value: unknown): number | undefined {
	const path = safePath(ctx, value);
	if (!path || path.startsWith("<external>")) return undefined;
	try {
		return Math.round(statSync(resolve(ctx.cwd, path)).mtimeMs);
	} catch {
		return undefined;
	}
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

function append(ctx: ExtensionContext, payload: { event: string } & Record<string, unknown>): void {
	if (!ctx.isProjectTrusted()) return;
	const cfg = config();
	mkdirSync(logDir, { recursive: true, mode: 0o700 });
	chmodSync(logDir, 0o700);
	const path = logPath();
	if (existsSync(path) && statSync(path).size >= cfg.maxBytesPerDay) return;
	const event: LogEvent = {
		ts: new Date().toISOString(),
		run: runId,
		repo: repoName(ctx),
		...payload,
	};
	appendFileSync(path, `${JSON.stringify(event)}\n`, { encoding: "utf8", mode: 0o600 });
	chmodSync(path, 0o600);
}

function commandClass(command: string): string {
	if (/(^|[;&|]\s*|\s)(rg|grep|find|fd|ls)(\s|$)/.test(command)) return "search";
	if (/\b(pytest|vitest|jest|cargo\s+test|go\s+test|just\s+(check|test|lint)|npm\s+test|bun\s+test)\b/.test(command)) {
		return "verify";
	}
	if (/(^|[;&|]\s*|\s)git(\s|$)/.test(command)) return "git";
	if (/\b(tsc|pyright|ruff|eslint|mypy)\b/.test(command)) return "analyze";
	return "other";
}

function toolMetadata(ctx: ExtensionContext, toolName: string, input: unknown): Record<string, unknown> {
	const record = input && typeof input === "object" ? (input as Record<string, unknown>) : {};
	if (toolName === "read") {
		return {
			path: safePath(ctx, record.path),
			offset: typeof record.offset === "number" ? record.offset : undefined,
			limit: typeof record.limit === "number" ? record.limit : undefined,
			mtime_ms: fileMtime(ctx, record.path),
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

function failureKind(output: string): string | undefined {
	const normalized = output.toLowerCase();
	if (normalized.includes("could not find") || normalized.includes("must match exactly")) return "edit-match-miss";
	if (normalized.includes("blocked by policy") || normalized.includes("protected path")) return "policy-block";
	if (normalized.includes("timed out") || normalized.includes("timeout")) return "timeout";
	if (normalized.includes("command exited with code")) return "nonzero-exit";
	return undefined;
}

function median(values: number[]): number {
	if (values.length === 0) return 0;
	const sorted = [...values].sort((a, b) => a - b);
	const middle = Math.floor(sorted.length / 2);
	return sorted.length % 2 === 0 ? (sorted[middle - 1] + sorted[middle]) / 2 : sorted[middle];
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
	const failures = ends.filter((event) => event.success === false);
	const zeroSearches = ends.filter((event) => event.class === "search" && event.result_lines === 0).length;
	const turns = events.filter((event) => event.event === "turn_end");
	const maxContext = Math.max(0, ...turns.map((event) => Number(event.context_tokens ?? 0)));
	const repeatedReads = reads.filter((event) => event.repeat_unchanged === true).length;
	const editBeforeRead = calls.filter((event) => event.edit_without_prior_read === true).length;
	const milestones = events.filter((event) => event.event === "first_mutation");
	const latency = milestones.map((event) => Number(event.latency_ms ?? 0)).filter((value) => value > 0);
	const callsBeforeMutation = milestones.map((event) => Number(event.prior_tool_calls ?? 0));
	const summaries = events.filter((event) => event.event === "session_summary" && event.mutated === true);
	const unverified = summaries.filter((event) => event.verified_after_mutation !== true).length;
	const failureCounts = new Map<string, number>();
	for (const event of failures) {
		const kind = String(event.failure_kind ?? "other");
		failureCounts.set(kind, (failureCounts.get(kind) ?? 0) + 1);
	}
	const failureSummary = [...failureCounts.entries()]
		.sort((a, b) => b[1] - a[1])
		.map(([kind, count]) => `${kind}:${count}`)
		.join(", ") || "none";
	const repos = new Set(events.map((event) => event.repo));
	const runs = new Set(events.map((event) => event.run));

	return [
		`Discovery telemetry (${repos.size} repo${repos.size === 1 ? "" : "s"}, ${runs.size} run${runs.size === 1 ? "" : "s"})`,
		`  Tool calls: ${calls.length}; reads: ${reads.length}`,
		`  Repeated unchanged reads: ${repeatedReads}; edit-before-read: ${editBeforeRead}`,
		`  First mutation: median ${(median(latency) / 1000).toFixed(1)}s, ${median(callsBeforeMutation).toFixed(0)} prior tools`,
		`  Failures: ${failures.length} (${failureSummary}); zero-result searches: ${zeroSearches}`,
		`  Mutating runs without verification: ${unverified}/${summaries.length}`,
		`  Peak context: ${Math.round(maxContext / 1000)}k tokens`,
		`  Raw logs: ${logDir}`,
	].join("\n");
}

export default function discoveryTelemetry(pi: ExtensionAPI) {
	let enabledOverride: boolean | undefined;
	const pending = new Map<string, { started: number; class?: string }[]>();
	const readKeys = new Set<string>();
	const readPaths = new Set<string>();
	const uniquePaths = new Set<string>();
	let sessionStarted = Date.now();
	let toolCalls = 0;
	let sessionReads = 0;
	let sessionSearches = 0;
	let sessionMutated = false;
	let verifiedAfterMutation = false;
	let firstMutationRecorded = false;
	let turnStarted = 0;
	let turnContextStart = 0;
	let turn = { tools: 0, reads: 0, searches: 0, mutations: 0, failures: 0, verifications: 0, routingReads: 0 };

	function enabled(): boolean {
		return enabledOverride ?? config().enabledByDefault;
	}

	function updateStatus(ctx: ExtensionContext): void {
		ctx.ui.setStatus(
			"discovery",
			enabled()
				? ctx.ui.theme.fg("accent", "telemetry ● on")
				: ctx.ui.theme.fg("dim", "telemetry ○ off"),
		);
	}

	function resetTurn(ctx: ExtensionContext): void {
		turnStarted = Date.now();
		turnContextStart = ctx.getContextUsage()?.tokens ?? 0;
		turn = { tools: 0, reads: 0, searches: 0, mutations: 0, failures: 0, verifications: 0, routingReads: 0 };
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
			updateStatus(ctx);
			ctx.ui.notify(
				`Discovery telemetry ${enabled() ? "ON" : "OFF"}\nLocal metadata only: ${logDir}`,
				"info",
			);
		},
	});

	pi.on("session_start", async (_event, ctx) => {
		cleanOldLogs(config().retentionDays);
		sessionStarted = Date.now();
		resetTurn(ctx);
		if (ctx.hasUI) updateStatus(ctx);
		if (enabled()) append(ctx, { event: "session_start" });
	});

	pi.on("turn_start", async (_event, ctx) => {
		if (enabled()) resetTurn(ctx);
	});

	pi.on("tool_call", async (event, ctx) => {
		if (!enabled()) return undefined;
		const toolName = event.toolName;
		const metadata = toolMetadata(ctx, toolName, event.input);
		const className = typeof metadata.class === "string" ? metadata.class : undefined;
		const path = typeof metadata.path === "string" ? metadata.path : undefined;
		const enriched: Record<string, unknown> = { ...metadata };
		toolCalls++;
		turn.tools++;

		if (path) uniquePaths.add(path);
		if (toolName === "read") {
			sessionReads++;
			turn.reads++;
			const key = [path, metadata.offset ?? "", metadata.limit ?? "", metadata.mtime_ms ?? ""].join(":");
			enriched.repeat_unchanged = readKeys.has(key);
			readKeys.add(key);
			if (path) {
				readPaths.add(path);
				const name = basename(path).toLowerCase();
				if (name === "agents.md" || name === "readme.md" || name === "_index.md" || path.includes("/docs/")) {
					turn.routingReads++;
					enriched.routing_doc = true;
				}
			}
		}

		if (className === "search") {
			sessionSearches++;
			turn.searches++;
		}
		if (className === "verify") {
			turn.verifications++;
			if (sessionMutated) verifiedAfterMutation = true;
		}

		if (toolName === "edit" || toolName === "write") {
			turn.mutations++;
			sessionMutated = true;
			if (toolName === "edit" && path) enriched.edit_without_prior_read = !readPaths.has(path);
			if (!firstMutationRecorded) {
				firstMutationRecorded = true;
				const usage = ctx.getContextUsage();
				append(ctx, {
					event: "first_mutation",
					latency_ms: Date.now() - sessionStarted,
					prior_tool_calls: Math.max(0, toolCalls - 1),
					prior_reads: sessionReads,
					prior_searches: sessionSearches,
					unique_paths: uniquePaths.size,
					context_tokens: usage?.tokens,
				});
			}
		}

		const queue = pending.get(toolName) ?? [];
		queue.push({ started: Date.now(), class: className });
		pending.set(toolName, queue);
		append(ctx, { event: "tool_call", tool: toolName, ...enriched });
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
		if (!success) turn.failures++;
		append(ctx, {
			event: "tool_end",
			tool: toolName,
			class: call?.class,
			success,
			failure_kind: success ? undefined : failureKind(output),
			duration_ms: call ? Date.now() - call.started : undefined,
			result_chars: output.length,
			result_lines: output ? output.split("\n").filter(Boolean).length : 0,
		});
	});

	pi.on("turn_end", async (_event, ctx) => {
		if (!enabled()) return;
		const usage = ctx.getContextUsage();
		const compactions = ctx.sessionManager
			.getEntries()
			.filter((entry) => entry.type === "compaction").length;
		append(ctx, {
			event: "turn_end",
			duration_ms: turnStarted ? Date.now() - turnStarted : undefined,
			tool_calls: turn.tools,
			reads: turn.reads,
			searches: turn.searches,
			mutations: turn.mutations,
			failures: turn.failures,
			verifications: turn.verifications,
			routing_reads: turn.routingReads,
			unique_paths: uniquePaths.size,
			context_tokens: usage?.tokens,
			context_percent: usage?.percent,
			context_growth: usage?.tokens == null ? undefined : usage.tokens - turnContextStart,
			compactions,
		});
	});

	pi.on("session_shutdown", async (_event, ctx) => {
		if (!enabled()) return;
		append(ctx, {
			event: "session_summary",
			duration_ms: Date.now() - sessionStarted,
			tool_calls: toolCalls,
			reads: sessionReads,
			searches: sessionSearches,
			unique_paths: uniquePaths.size,
			mutated: sessionMutated,
			verified_after_mutation: verifiedAfterMutation,
		});
		append(ctx, { event: "session_shutdown" });
	});
}
