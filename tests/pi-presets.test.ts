import { describe, expect, mock, test } from "bun:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

mock.module("@earendil-works/pi-coding-agent", () => ({ getAgentDir: () => "/tmp/pi-agent" }));
const { isConnectorTool, presetCanAct } = await import("../agents/pi/extensions/presets");

describe("Pi preset taint guard", () => {
	test("classifies connector tools as untrusted-content sources", () => {
		for (const tool of [
			"gmail_search_threads",
			"calendar_list_events",
			"strava_get_activity",
			"apple_notes_get",
			"granola_tool",
		]) {
			expect(isConnectorTool(tool)).toBe(true);
		}
		for (const tool of ["read", "bash", "grep", "edit"]) {
			expect(isConnectorTool(tool)).toBe(false);
		}
	});

	test("identifies acting presets by shell/edit/write tools", () => {
		expect(presetCanAct({ tools: ["read", "grep", "bash"] })).toBe(true);
		expect(presetCanAct({ tools: ["read", "grep", "edit", "write"] })).toBe(true);
		expect(presetCanAct({ tools: ["apple_notes_create"] })).toBe(true);
		expect(presetCanAct({ tools: ["read", "grep", "gmail_search_threads"] })).toBe(false);
		expect(presetCanAct({})).toBe(false);
	});

	test("lets dev sessions manage one bounded worker autonomously", () => {
		const path = resolve(import.meta.dir, "../agents/pi/presets.json");
		const presets = JSON.parse(readFileSync(path, "utf8")) as {
			dev: { tools: string[]; instructions: string };
		};
		expect(presets.dev.tools).toContain("worker");
		expect(presets.dev.instructions).toContain("Autonomously call the worker tool");
		expect(presets.dev.instructions).toContain("no user approval is required");
		expect(presets.dev.instructions).toContain("Do not delegate small tasks");
	});

	test("uses Pi's native fullscreen transcript instead of a custom reader", () => {
		const path = resolve(import.meta.dir, "../agents/pi/settings.json");
		const settings = JSON.parse(readFileSync(path, "utf8")) as { tuiMode?: string };
		expect(settings.tuiMode).toBe("fullscreen");
	});
});
