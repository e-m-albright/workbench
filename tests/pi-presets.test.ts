import { describe, expect, mock, test } from "bun:test";

mock.module("@earendil-works/pi-coding-agent", () => ({ getAgentDir: () => "/tmp/pi-agent" }));
const { isConnectorTool, presetCanAct } = await import("../agents/pi/extensions/presets");

describe("Pi preset taint guard", () => {
	test("classifies connector tools as untrusted-content sources", () => {
		for (const tool of ["gmail_search_threads", "calendar_list_events", "strava_get_activity", "granola_tool"]) {
			expect(isConnectorTool(tool)).toBe(true);
		}
		for (const tool of ["read", "bash", "grep", "edit"]) {
			expect(isConnectorTool(tool)).toBe(false);
		}
	});

	test("identifies acting presets by shell/edit/write tools", () => {
		expect(presetCanAct({ tools: ["read", "grep", "bash"] })).toBe(true);
		expect(presetCanAct({ tools: ["read", "grep", "edit", "write"] })).toBe(true);
		expect(presetCanAct({ tools: ["read", "grep", "gmail_search_threads"] })).toBe(false);
		expect(presetCanAct({})).toBe(false);
	});
});
