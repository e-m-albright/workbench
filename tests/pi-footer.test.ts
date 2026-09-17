import { expect, vi, test } from "vitest";

vi.doMock("@earendil-works/pi-tui", () => ({
	truncateToWidth: (value: string) => value,
	visibleWidth: (value: string) => value.replace(/\x1b\[[0-9;]*m/g, "").length,
}));
const { formatCodexQuota, renderFooter } = await import("../agents/pi/extensions/footer");

test.each([
	[80, "restricted"],
	[120, "restricted"],
	[80, "unrestricted"],
	[120, "unrestricted"],
] as const)("footer at %i columns shows %s authority", (width, authority) => {
	vi.stubEnv("NO_COLOR", "1");
	vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", authority);
	vi.stubEnv("WORKBENCH_AGENT_LOCATION", "hosted");
	vi.stubEnv("WORKBENCH_HOST_HOME", "/example");
	try {
		const ctx = {
			cwd: "/example/code/project",
			ui: { theme: {} },
			sessionManager: { getEntries: () => [] },
			getContextUsage: () => ({ percent: 0, tokens: 0, contextWindow: 272000 }),
			model: { provider: "openai-codex", id: "model", contextWindow: 272000 },
			modelRegistry: { isUsingOAuth: () => true },
		} as Parameters<typeof renderFooter>[0];
		const lines = renderFooter(ctx, { kind: "not-git" }, { kind: "unknown" }, width);
		expect(lines).toHaveLength(2);
		expect(lines[0]).toContain("~/code/project");
		expect(lines[0]).toContain(`hosted > ${authority}`);
		expect(lines[1]).toContain("ctx 0.0% 0/272k");
		expect(lines[1]).toContain("openai-codex/model");
	} finally {
		vi.unstubAllEnvs();
	}
});

test("Codex quota labels and colorizes remaining capacity", () => {
	const previous = process.env.NO_COLOR;
	delete process.env.NO_COLOR;
	try {
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
	} finally {
		if (previous === undefined) delete process.env.NO_COLOR;
		else process.env.NO_COLOR = previous;
	}
});
