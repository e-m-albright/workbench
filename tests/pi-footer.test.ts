import { expect, mock, test } from "bun:test";

mock.module("@earendil-works/pi-tui", () => ({
	truncateToWidth: (value: string) => value,
	visibleWidth: (value: string) => value.replace(/\x1b\[[0-9;]*m/g, "").length,
}));
const { formatCodexQuota } = await import("../agents/pi/extensions/git-status");

test("Codex quota shows remaining percentages, windows, and reset dates", () => {
	const value = formatCodexQuota(
		{
			kind: "codex",
			secondary: { usedPercent: 40, windowDurationMins: 300, resetsAt: 1_785_000_000 },
			primary: { usedPercent: 18, windowDurationMins: 10_080, resetsAt: 1_785_280_704 },
		},
		new Date("2026-07-21T12:00:00-07:00"),
	);

	expect(value).toContain("5h 60%");
	expect(value).toContain("1w 82%");
	expect(value).toContain("→");
});
