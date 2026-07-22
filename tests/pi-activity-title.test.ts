import { expect, test } from "bun:test";
import { deriveThreadTitle, formatActivityTitle } from "../agents/pi/extensions/activity-title";

test("thread titles remove conversational boilerplate and stay compact", () => {
	expect(deriveThreadTitle("Could you please review the OAuth adapter failures and fix them?"))
		.toBe("review the OAuth adapter failures and fix");
	expect(deriveThreadTitle("Look for community builds in Pi too, to get ideas."))
		.toBe("community builds in Pi too, to get");
	expect(deriveThreadTitle("https://example.com")).toBe("new session");
	expect(deriveThreadTitle("Investigate this extremely detailed and deliberately overlong transcript navigation failure now"))
		.toBe("Investigate this extremely detailed and…");
});

test("activity titles put progress, project, thread, and tool in scan order", () => {
	expect(formatActivityTitle("notes", "Pi harness improvements", "⠹", "read"))
		.toBe("⠹ notes / Pi harness improvements · read");
	expect(formatActivityTitle("notes", undefined)).toBe("π notes");
});
