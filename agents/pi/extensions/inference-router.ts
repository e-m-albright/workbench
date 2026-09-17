import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { resolveAgentDir } from "./lib/agent-dir";

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
	frontier: { provider: "openai-codex", model: "gpt-5.6-sol" },
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

function loadConfig(cwd: string): RouterConfig {
	const global = mergeConfig(DEFAULT_CONFIG, readConfig(join(resolveAgentDir(), "inference-router.json")));
	const merged = mergeConfig(global, readConfig(join(cwd, ".pi", "inference-router.json")));
	if (merged.private.provider !== "omlx")
		throw new Error("Private inference requires the local oMLX provider");
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
	const mode = process.env.WORKBENCH_PI_MODE;
	const pinnedRoute: Route | undefined = mode?.startsWith("local-")
		? "private"
		: mode?.startsWith("hosted-")
			? "frontier"
			: undefined;

	async function selectRoute(next: Route, ctx: ExtensionContext): Promise<boolean> {
		if (!configValid) return false;
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
					"The launch mode fixes inference location. Start a new session to change modes.",
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
		try {
			config = loadConfig(ctx.cwd);
			configValid = true;
		} catch (error) {
			ctx.ui.notify(`Inference routing blocked: ${String(error)}`, "error");
			return;
		}
		route = pinnedRoute ?? routeFrom(pi.getFlag("route"), config.defaultMode);
		stickyPrivate = route === "private";
		// The launch fixes location, while --model and desktop profiles select a model within it.
		const current = ctx.model;
		routeReady = Boolean(
			current && (route === "private" ? current.provider === "omlx" : current.provider !== "omlx"),
		);
		if (!routeReady) routeReady = await selectRoute(route, ctx);
	});

	pi.on("model_select", async (_event, ctx) => {
		if (route === "private" && ctx.model?.provider !== "omlx") routeReady = await selectRoute("private", ctx);
		if (pinnedRoute === "frontier" && ctx.model?.provider === "omlx")
			routeReady = await selectRoute("frontier", ctx);
	});

	pi.on("input", async (event, ctx) => {
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
