import { expect, mock, test } from "bun:test";

mock.module("@earendil-works/pi-tui", () => ({
	truncateToWidth: (value: string) => value,
	visibleWidth: (value: string) => value.replace(/\x1b\[[0-9;]*m/g, "").length,
}));
const { formatCodexQuota } = await import("../agents/pi/extensions/footer");

test("Codex quota labels and colorizes remaining capacity", () => {
	const value = formatCodexQuota(
		{
			kind: "codex",
			secondary: { usedPercent: 73, windowDurationMins: 300, resetsAt: 1_785_000_000 },
			primary: { usedPercent: 93, windowDurationMins: 10_080, resetsAt: 1_785_280_704 },
		},
		new Date("2026-07-21T12:00:00-07:00"),
	);
	const plain = value.replace(/\x1b\[[0-9;]*m/g, "");

	expect(plain).toContain("5h 27% left");
	expect(plain).toContain("1w 7% left");
	expect(value).toContain("\x1b[38;2;211;177;95m27% left");
	expect(value).toContain("\x1b[38;2;184;86;105m7% left");
	expect(plain).toContain("→");
});
