import { expect, test, vi } from "vitest";

vi.doMock("@earendil-works/pi-tui", () => ({
	truncateToWidth: (value: string) => value,
	visibleWidth: (value: string) => value.replace(/\x1b\[[0-9;]*m/g, "").length,
}));
const {
	default: footerExtension,
	formatCodexQuota,
	renderFooter,
} = await import("../agents/pi/extensions/footer");

function footerHarness() {
	const handlers = new Map<string, (...args: any[]) => any>();
	let footer: { render(width: number): string[] };
	let entries: any[] = [];
	const ctx = {
		cwd: "/example/project",
		hasUI: true,
		ui: {
			theme: {},
			setFooter: (factory: any) => {
				footer = factory({ requestRender() {} }, {}, {});
			},
		},
		sessionManager: { getEntries: () => entries },
		getContextUsage: () => ({ percent: 0, tokens: 0, contextWindow: 272000 }),
		model: { provider: "openai-codex", id: "model", contextWindow: 272000 },
		modelRegistry: { isUsingOAuth: () => true },
	};
	const exec = vi.fn(async (_cmd: string, args: string[], _options?: { cwd: string }) => ({
		code: 0,
		stdout: args.includes("--is-inside-work-tree")
			? "true\n"
			: args.includes("--porcelain")
				? " M file\n"
				: args.includes("symbolic-ref")
					? "main\n"
					: "",
		stderr: "",
	}));
	footerExtension({
		on: (name: string, fn: any) => handlers.set(name, fn),
		exec,
	} as any);
	return {
		ctx,
		handlers,
		exec,
		render: () => footer.render(1000).join("\n"),
		setEntries: (value: any[]) => {
			entries = value;
		},
	};
}

test("a slow previous-session refresh cannot replace the current footer", async () => {
	vi.stubEnv("NO_COLOR", "1");
	vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "restricted");
	const harness = footerHarness();
	let finish!: (result: { code: number; stdout: string; stderr: string }) => void;
	harness.exec.mockImplementationOnce(
		() =>
			new Promise((resolve) => {
				finish = resolve;
			}),
	);
	try {
		const previous = harness.handlers.get("session_start")?.({}, harness.ctx);
		await harness.handlers.get("session_start")?.({}, { ...harness.ctx, cwd: "/example/current" });
		finish({ code: 0, stdout: "true\n", stderr: "" });
		await previous;
		expect(harness.render()).toContain("/example/current");
		expect(harness.render()).not.toContain("/example/project");
	} finally {
		await harness.handlers.get("session_shutdown")?.();
		vi.unstubAllEnvs();
	}
});

test("footer preserves the unstaged column in the first porcelain record", async () => {
	vi.stubEnv("NO_COLOR", "1");
	vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "restricted");
	const harness = footerHarness();
	try {
		await harness.handlers.get("session_start")?.({}, harness.ctx);
		expect(harness.render()).toContain("main *1");
		expect(harness.render()).not.toContain("+1");
	} finally {
		await harness.handlers.get("session_shutdown")?.();
		vi.unstubAllEnvs();
	}
});

test("a new footer session discards previous speed and quota telemetry", async () => {
	vi.useFakeTimers();
	vi.setSystemTime(1000);
	vi.stubEnv("NO_COLOR", "1");
	vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "restricted");
	const harness = footerHarness();
	try {
		await harness.handlers.get("session_start")?.({}, harness.ctx);
		await harness.handlers.get("after_provider_response")?.(
			{ headers: { "x-ratelimit-limit-tokens": "100", "x-ratelimit-remaining-tokens": "60" } },
			harness.ctx,
		);
		await harness.handlers.get("turn_start")?.({}, harness.ctx);
		vi.setSystemTime(2000);
		harness.setEntries([
			{
				type: "message",
				message: {
					role: "assistant",
					usage: { output: 100, input: 0, cacheRead: 0, cacheWrite: 0, cost: { total: 0 } },
				},
			},
		]);
		await harness.handlers.get("turn_end")?.({}, harness.ctx);
		expect(harness.render()).toContain("100 tok/s");
		expect(harness.render()).toContain("60% left");
		harness.setEntries([]);
		await harness.handlers.get("session_start")?.({}, harness.ctx);
		expect(harness.render()).not.toContain("tok/s");
		expect(harness.render()).not.toContain("% left");
	} finally {
		await harness.handlers.get("session_shutdown")?.();
		vi.unstubAllEnvs();
		vi.useRealTimers();
	}
});

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
