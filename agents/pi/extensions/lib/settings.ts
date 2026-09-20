import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { ExtensionContext } from "@earendil-works/pi-coding-agent";
import { resolveAgentDir } from "./agent-dir";

function object(value: unknown): Record<string, unknown> {
	return value !== null && typeof value === "object" && !Array.isArray(value)
		? (value as Record<string, unknown>)
		: {};
}

function readSettings(path: string, section?: string): Record<string, unknown> {
	if (!existsSync(path)) return {};
	const settings = object(JSON.parse(readFileSync(path, "utf8")));
	return section ? object(settings[section]) : settings;
}

// Pi exposes project trust, but not its settings manager, to extensions.
// Merge one flat settings section; consumers validate the values they own.
export function loadSettings(ctx: Pick<ExtensionContext, "cwd" | "isProjectTrusted">, section?: string) {
	return {
		...readSettings(join(resolveAgentDir(), "settings.json"), section),
		...(ctx.isProjectTrusted?.() === true
			? readSettings(join(ctx.cwd, ".pi", "settings.json"), section)
			: {}),
	};
}
