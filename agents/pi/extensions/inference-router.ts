import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { resolveAgentDir } from "./lib/agent-dir";

export type RouteMode = "frontier" | "private" | "auto";
export type Route = "frontier" | "private";
export type RouteReason =
	| "private_workspace"
	| "personal_data"
	| "simple"
	| "coding"
	| "complex"
	| "uncertain"
	| "classifier_unavailable"
	| "sensitive_tool";

interface ModelTarget {
	provider: string;
	model: string;
}

export interface RouterConfig {
	defaultMode: RouteMode;
	frontier: ModelTarget;
	private: ModelTarget;
	classifier: {
		baseUrl: string;
		model: string;
		timeoutMs: number;
	};
	privatePathFragments: string[];
}

export interface RouteDecision {
	route: Route;
	reason: RouteReason;
}

const DEFAULT_CONFIG: RouterConfig = {
	defaultMode: "frontier",
	frontier: { provider: "openai-codex", model: "gpt-5.6-sol" },
	private: { provider: "omlx", model: "Qwen3.6-35B-A3B-oQ4e-mtp" },
	classifier: {
		baseUrl: "http://localhost:8000/v1",
		model: "Qwen3.6-35B-A3B-oQ4e-mtp",
		timeoutMs: 1500,
	},
	privatePathFragments: ["/code/private/"],
};

const PERSONAL_DATA_PATTERN =
	/\b(task queue|my notes?|apple notes?|email|gmail|calendar|contacts?|journal|health|medical|therapy|family|finances?|bank|relationship|rolodex|crm|meeting history)\b/i;
const CONNECTOR_PREFIXES = [
	"gmail_",
	"calendar_",
	"strava_",
	"apple_notes_",
	"apple_contacts_",
	"contacts_",
	"granola",
	"notes_sources",
];
const CLASSIFIER_REASONS = new Set<RouteReason>([
	"personal_data",
	"simple",
	"coding",
	"complex",
	"uncertain",
]);

function readConfig(path: string): Partial<RouterConfig> {
	if (!existsSync(path)) return {};
	return JSON.parse(readFileSync(path, "utf8")) as Partial<RouterConfig>;
}

function mergeConfig(base: RouterConfig, override: Partial<RouterConfig>): RouterConfig {
	return {
		...base,
		...override,
		frontier: { ...base.frontier, ...override.frontier },
		private: { ...base.private, ...override.private },
		classifier: { ...base.classifier, ...override.classifier },
		privatePathFragments: override.privatePathFragments ?? base.privatePathFragments,
	};
}

function loadConfig(cwd: string): RouterConfig {
	const global = mergeConfig(DEFAULT_CONFIG, readConfig(join(resolveAgentDir(), "inference-router.json")));
	return mergeConfig(global, readConfig(join(cwd, ".pi", "inference-router.json")));
}

function pathIsPrivate(path: string, config: RouterConfig): boolean {
	const normalized = path.toLowerCase();
	return config.privatePathFragments.some((fragment) => normalized.includes(fragment.toLowerCase()));
}

export function classifyHardRule(text: string, cwd: string, config: RouterConfig): RouteDecision | undefined {
	if (pathIsPrivate(cwd, config)) return { route: "private", reason: "private_workspace" };
	if (PERSONAL_DATA_PATTERN.test(text)) return { route: "private", reason: "personal_data" };
	return undefined;
}

export function parseClassifierDecision(content: string): RouteDecision | undefined {
	try {
		const value = JSON.parse(content) as { route?: unknown; reason?: unknown };
		if (value.route !== "private" && value.route !== "frontier") return undefined;
		if (typeof value.reason !== "string" || !CLASSIFIER_REASONS.has(value.reason as RouteReason))
			return undefined;
		return { route: value.route, reason: value.reason as RouteReason };
	} catch {
		return undefined;
	}
}

export function isSensitiveToolCall(
	toolName: string,
	input: Record<string, unknown>,
	config: RouterConfig,
): boolean {
	if (CONNECTOR_PREFIXES.some((prefix) => toolName.startsWith(prefix))) return true;

	if (["read", "edit", "write"].includes(toolName)) {
		const path = typeof input.path === "string" ? input.path : "";
		return pathIsPrivate(path, config);
	}

	if (toolName === "bash") {
		const command = typeof input.command === "string" ? input.command : "";
		if (/(?:^|[;&|\s])notes(?:\s|$)/.test(command)) return true;
		return config.privatePathFragments.some((fragment) =>
			command.toLowerCase().includes(fragment.toLowerCase()),
		);
	}

	return false;
}

async function classifyLocally(text: string, config: RouterConfig): Promise<RouteDecision | undefined> {
	const controller = new AbortController();
	const timeout = setTimeout(() => controller.abort(), config.classifier.timeoutMs);
	try {
		const response = await fetch(`${config.classifier.baseUrl.replace(/\/$/, "")}/chat/completions`, {
			method: "POST",
			headers: { "content-type": "application/json" },
			body: JSON.stringify({
				model: config.classifier.model,
				temperature: 0,
				max_tokens: 32,
				chat_template_kwargs: { enable_thinking: false },
				response_format: {
					type: "json_schema",
					json_schema: {
						name: "route_decision",
						strict: true,
						schema: {
							type: "object",
							additionalProperties: false,
							required: ["route", "reason"],
							properties: {
								route: { type: "string", enum: ["private", "frontier"] },
								reason: {
									type: "string",
									enum: ["personal_data", "simple", "coding", "complex", "uncertain"],
								},
							},
						},
					},
				},
				messages: [
					{
						role: "system",
						content:
							'Classify exactly one user request for inference routing. FRONTIER: any request to write, edit, review, explain, or debug code; or unusually complex reasoning. PRIVATE: personal or confidential data, ordinary conversation, summaries, comparisons, and simple questions. Examples: "Write a Python function" => {"route":"frontier","reason":"coding"}. "Debug this code" => {"route":"frontier","reason":"coding"}. "Prove a difficult theorem" => {"route":"frontier","reason":"complex"}. "Summarize this" => {"route":"private","reason":"simple"}. "Read my medical notes" => {"route":"private","reason":"personal_data"}. When uncertain return {"route":"private","reason":"uncertain"}. Return only the required JSON.',
					},
					{ role: "user", content: text },
				],
			}),
			signal: controller.signal,
		});
		if (!response.ok) return undefined;
		const payload = (await response.json()) as {
			choices?: Array<{ message?: { content?: string } }>;
		};
		const content = payload.choices?.[0]?.message?.content;
		return typeof content === "string" ? parseClassifierDecision(content) : undefined;
	} catch {
		return undefined;
	} finally {
		clearTimeout(timeout);
	}
}

function modeFrom(value: unknown, fallback: RouteMode): RouteMode {
	return value === "frontier" || value === "private" || value === "auto" ? value : fallback;
}

function reasonLabel(reason: RouteReason): string {
	return reason.replaceAll("_", " ");
}

export function formatRouteLabel(mode: RouteMode, decision?: RouteDecision): string {
	if (!decision || mode !== "auto") return mode;
	return `${mode} → ${decision.route} (${reasonLabel(decision.reason)})`;
}

export default function inferenceRouterExtension(pi: ExtensionAPI) {
	let config = DEFAULT_CONFIG;
	let mode: RouteMode = "frontier";
	let decision: RouteDecision | undefined;
	let stickyPrivate = false;
	let privateRouteReady = true;

	function setStatus(ctx: ExtensionContext) {
		const theme = ctx.ui.theme;
		const target = (route: Route) => theme.fg(route === "private" ? "success" : "accent", route);
		let label = theme.fg("dim", "route ");
		if (mode !== "auto") {
			label += target(mode);
		} else {
			label += theme.fg("warning", "auto");
			if (decision) {
				label += theme.fg("dim", " → ");
				label += target(decision.route);
				label += theme.fg("dim", ` (${reasonLabel(decision.reason)})`);
			}
		}
		ctx.ui.setStatus("inference-route", label);
	}

	async function selectTarget(route: Route, ctx: ExtensionContext): Promise<boolean> {
		const target = route === "private" ? config.private : config.frontier;
		const model = ctx.modelRegistry.find(target.provider, target.model);
		if (!model) {
			ctx.ui.notify(`Route ${route}: model not found: ${target.provider}/${target.model}`, "warning");
			return false;
		}
		const selected = await pi.setModel(model);
		if (!selected) {
			ctx.ui.notify(`Route ${route}: model unavailable: ${target.provider}/${target.model}`, "warning");
			return false;
		}
		return true;
	}

	async function applyDecision(next: RouteDecision, ctx: ExtensionContext): Promise<boolean> {
		if (stickyPrivate && next.route === "frontier") {
			next = { route: "private", reason: "personal_data" };
		}
		if (next.route === "private") stickyPrivate = true;
		if (!(await selectTarget(next.route, ctx))) {
			if (next.route === "private") privateRouteReady = false;
			return false;
		}
		if (next.route === "private") privateRouteReady = true;
		decision = next;
		setStatus(ctx);
		return true;
	}

	pi.registerFlag("route", {
		description: "Inference route: frontier, private, or auto",
		type: "string",
	});

	pi.registerCommand("route", {
		description: "Select inference route: frontier, private, or auto",
		handler: async (args, ctx) => {
			const requested = args.trim();
			let next: RouteMode | undefined;
			if (requested) {
				next = modeFrom(requested, "auto");
				if (next !== requested) {
					ctx.ui.notify(`Unknown route: ${requested}`, "warning");
					return;
				}
			} else {
				const selected = await ctx.ui.select("Inference route", ["frontier", "private", "auto"]);
				if (!selected) return;
				next = selected as RouteMode;
			}

			if (next === "frontier" && stickyPrivate) {
				const confirmed = await ctx.ui.confirm(
					"Private context in session",
					"This session has been routed privately. Sending it to a frontier provider may expose accumulated context. Switch anyway?",
				);
				if (!confirmed) return;
			}

			mode = next;
			decision = undefined;
			stickyPrivate = next === "private";
			if (
				next !== "auto" &&
				!(await applyDecision({ route: next, reason: next === "private" ? "personal_data" : "coding" }, ctx))
			)
				return;
			setStatus(ctx);
			ctx.ui.notify(`Inference route: ${next}`, "info");
		},
	});

	pi.on("session_start", async (_event, ctx) => {
		config = loadConfig(ctx.cwd);
		mode = modeFrom(pi.getFlag("route"), config.defaultMode);
		decision = undefined;
		stickyPrivate = mode === "private";
		privateRouteReady = true;
		if (mode !== "auto") {
			await applyDecision({ route: mode, reason: mode === "private" ? "personal_data" : "coding" }, ctx);
		}
		setStatus(ctx);
	});

	pi.on("input", async (event, ctx) => {
		if (event.source === "extension") return { action: "continue" as const };
		if (mode === "private" && !privateRouteReady) {
			if (await applyDecision({ route: "private", reason: "private_workspace" }, ctx)) {
				return { action: "continue" as const };
			}
			ctx.ui.setEditorText(event.text);
			ctx.ui.notify("Private route blocked: the local model is unavailable", "error");
			return { action: "handled" as const };
		}
		if (mode !== "auto") return { action: "continue" as const };
		if (stickyPrivate) {
			if (await applyDecision({ route: "private", reason: "personal_data" }, ctx)) {
				return { action: "continue" as const };
			}
			ctx.ui.setEditorText(event.text);
			return { action: "handled" as const };
		}

		const hardRule = classifyHardRule(event.text, ctx.cwd, config);
		const next = hardRule ??
			(await classifyLocally(event.text, config)) ?? {
				route: "private" as const,
				reason: "classifier_unavailable" as const,
			};
		if (await applyDecision(next, ctx)) return { action: "continue" as const };

		// Auto mode fails closed: preserve the prompt for retry rather than silently
		// sending it to the currently selected frontier model.
		ctx.ui.setEditorText(event.text);
		ctx.ui.notify("Auto route blocked: the private model is unavailable", "error");
		return { action: "handled" as const };
	});

	pi.on("tool_call", async (event, ctx) => {
		if (mode !== "auto" || stickyPrivate) return;
		if (!isSensitiveToolCall(event.toolName, event.input as Record<string, unknown>, config)) return;
		const next: RouteDecision = { route: "private", reason: "sensitive_tool" };
		if (await applyDecision(next, ctx)) return;
		return {
			block: true,
			reason: "Sensitive tool result cannot be exposed because the private model is unavailable",
			terminate: true,
		};
	});
}
