import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { type ExtensionAPI, type ExtensionContext, parseArgs } from "@earendil-works/pi-coding-agent";
import { resolveAgentDir } from "./lib/agent-dir";
import { loadSettings } from "./lib/settings";

export type Route = "frontier" | "private";

interface ModelTarget {
	provider: string;
	model: string;
}

export interface RouterConfig {
	defaultMode: Route;
	frontier: ModelTarget;
	private: ModelTarget;
}

const DEFAULT_CONFIG: RouterConfig = {
	defaultMode: "frontier",
	frontier: { provider: "openai-codex", model: "gpt-6.1-sol" },
	private: { provider: "omlx", model: "Qwen3.6-35B-A3B-oQ4e-mtp" },
};

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
	};
}

function loadConfig(ctx: ExtensionContext): RouterConfig {
	const settings = loadSettings(ctx);
	const hostedDefault = typeof settings.defaultProvider === "string" && settings.defaultProvider !== "omlx";
	const defaults = {
		...DEFAULT_CONFIG,
		frontier: hostedDefault
			? {
					provider: settings.defaultProvider as string,
					model:
						typeof settings.defaultModel === "string" ? settings.defaultModel : DEFAULT_CONFIG.frontier.model,
				}
			: DEFAULT_CONFIG.frontier,
	};
	const global = mergeConfig(defaults, readConfig(join(resolveAgentDir(), "inference-router.json")));
	const merged = mergeConfig(
		global,
		ctx.isProjectTrusted?.() === true ? readConfig(join(ctx.cwd, ".pi", "inference-router.json")) : {},
	);
	if (merged.private.provider !== "omlx")
		throw new Error("Private inference requires the local oMLX provider");
	if (merged.frontier.provider === "omlx") throw new Error("Frontier inference requires a hosted provider");
	return merged;
}

function routeFrom(value: unknown, fallback: Route): Route {
	return value === "frontier" || value === "private" ? value : fallback;
}

export default function inferenceRouterExtension(pi: ExtensionAPI) {
	let config = DEFAULT_CONFIG;
	let route: Route = "frontier";
	let stickyPrivate = false;
	let routeReady = false;
	let configValid = false;
	let startupBlocked = false;
	const blockedMessage =
		"Managed sessions cannot honor private inference. Start pi --route private from your host terminal; no input will be submitted in this session.";
	const managed =
		process.env.WORKBENCH_PI_MODE === "hosted-managed" || process.env.WORKBENCH_AGENT_AUTHORITY === "managed";
	const pinnedRoute: Route | undefined = managed ? "frontier" : undefined;

	async function selectRoute(next: Route, ctx: ExtensionContext): Promise<boolean> {
		if (!configValid || startupBlocked) return false;
		const target = config[next];
		const model = ctx.modelRegistry.find(target.provider, target.model);
		if (!model) {
			ctx.ui.notify(`Route ${next}: model not found: ${target.provider}/${target.model}`, "warning");
			return false;
		}
		if (!(await pi.setModel(model))) {
			ctx.ui.notify(`Route ${next}: model unavailable: ${target.provider}/${target.model}`, "warning");
			return false;
		}
		route = next;
		if (next === "private") stickyPrivate = true;
		routeReady = true;
		return true;
	}

	pi.registerFlag("route", {
		description: "Inference route: frontier or private",
		type: "string",
	});

	pi.registerCommand("route", {
		description: "Select inference route: frontier or private",
		handler: async (args, ctx) => {
			if (startupBlocked) {
				ctx.ui.notify(blockedMessage, "error");
				return;
			}
			const requested = args.trim();
			let next: Route | undefined;
			if (requested) {
				if (requested !== "frontier" && requested !== "private") {
					ctx.ui.notify(`Unknown route: ${requested}`, "warning");
					return;
				}
				next = requested;
			} else {
				const selected = await ctx.ui.select("Inference route", ["frontier", "private"]);
				if (!selected) return;
				next = selected as Route;
			}

			if ((pinnedRoute && next !== pinnedRoute) || (next === "frontier" && stickyPrivate)) {
				ctx.ui.notify(
					"Managed sessions use cloud inference, and private sessions cannot switch to cloud. Start a new native pi session to change inference location.",
					"error",
				);
				return;
			}
			if (await selectRoute(next, ctx)) ctx.ui.notify(`Inference route: ${next}`, "info");
		},
	});

	pi.on("session_start", async (_event, ctx) => {
		routeReady = false;
		configValid = false;
		// Use the vendor parser so prompt text and restored models are not mistaken for flags.
		const startup = managed ? parseArgs(process.argv.slice(2)) : undefined;
		startupBlocked = Boolean(
			managed &&
				(pi.getFlag("route") === "private" ||
					startup?.provider === "omlx" ||
					(startup?.model && (ctx.model?.provider === "omlx" || startup.model.startsWith("omlx/")))),
		);
		if (startupBlocked) {
			ctx.ui.notify(blockedMessage, "error");
			return;
		}
		try {
			config = loadConfig(ctx);
			configValid = true;
		} catch (error) {
			ctx.ui.notify(`Inference routing blocked: ${String(error)}`, "error");
			return;
		}
		route =
			pinnedRoute ??
			routeFrom(pi.getFlag("route"), ctx.model?.provider === "omlx" ? "private" : config.defaultMode);
		stickyPrivate = route === "private";
		// Managed sessions pin cloud inference; native startup models retain their location.
		const current = ctx.model;
		routeReady = Boolean(
			current && (route === "private" ? current.provider === "omlx" : current.provider !== "omlx"),
		);
		if (!routeReady) routeReady = await selectRoute(route, ctx);
	});

	pi.on("model_select", async (_event, ctx) => {
		if (startupBlocked) return;
		if (!managed && ctx.model?.provider === "omlx") {
			route = "private";
			stickyPrivate = true;
			routeReady = configValid;
		}
		if (route === "private" && ctx.model?.provider !== "omlx") routeReady = await selectRoute("private", ctx);
		if (pinnedRoute === "frontier" && ctx.model?.provider === "omlx")
			routeReady = await selectRoute("frontier", ctx);
	});

	pi.on("input", async (event, ctx) => {
		if (startupBlocked) {
			ctx.ui.setEditorText(event.text);
			ctx.ui.notify(blockedMessage, "error");
			return { action: "handled" as const };
		}
		if (routeReady && (route !== "private" || ctx.model?.provider === "omlx"))
			return { action: "continue" as const };
		if (await selectRoute(route, ctx)) return { action: "continue" as const };
		ctx.ui.setEditorText(event.text);
		ctx.ui.notify(
			`${route === "private" ? "Private" : "Frontier"} route blocked: model unavailable`,
			"error",
		);
		return { action: "handled" as const };
	});
}
