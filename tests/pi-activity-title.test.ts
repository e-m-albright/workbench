import { expect, mock, test } from "bun:test";

mock.module("@earendil-works/pi-tui", () => ({
	truncateToWidth: (value: string, width: number, ellipsis = "…") =>
		value.length <= width ? value : `${value.slice(0, Math.max(0, width - ellipsis.length))}${ellipsis}`,
	visibleWidth: (value: string) => value.length,
}));

const {
	default: activityTitle,
	deriveThreadTitle,
	formatActivityLine,
	formatActivityTitle,
	formatElapsed,
	normalizePhase,
} = await import("../agents/pi/extensions/activity-title");

test("thread titles remove conversational boilerplate and stay compact", () => {
	expect(deriveThreadTitle("Could you please review the OAuth adapter failures and fix them?")).toBe(
		"review the OAuth adapter failures and fix",
	);
	expect(deriveThreadTitle("Look for community builds in Pi too, to get ideas.")).toBe(
		"community builds in Pi too, to get",
	);
	expect(deriveThreadTitle("https://example.com")).toBe("new session");
	expect(
		deriveThreadTitle(
			"Investigate this extremely detailed and deliberately overlong transcript navigation failure now",
		),
	).toBe("Investigate this extremely detailed and…");
});

test("activity titles put progress, project, thread, and phase in scan order", () => {
	expect(formatActivityTitle("notes", "Pi harness improvements", "⠹", "Running focused tests")).toBe(
		"⠹ notes | Pi harness improvements · Running focused tests",
	);
	expect(formatActivityTitle("notes", undefined)).toBe("π notes");
});

test("activity phases stay compact and single-line", () => {
	expect(normalizePhase("  Running\n focused\t tests  ")).toBe("Running focused tests");
	expect(normalizePhase("x".repeat(100))).toBe(`${"x".repeat(71)}…`);
	expect(normalizePhase("   ")).toBe("Working");
});

test("elapsed time uses stable compact units", () => {
	expect(formatElapsed(4_000)).toBe("0m");
	expect(formatElapsed(9 * 60_000)).toBe("9m");
	expect(formatElapsed(68 * 60_000)).toBe("1h 08m");
	expect(formatElapsed(26 * 60 * 60_000)).toBe("1d 02h");
});

test("activity line keeps total elapsed time fixed at the right edge", () => {
	const line = formatActivityLine("Running repository checks", "1h 08m", 52, "⠹");
	expect(line).toBe("⠹ Running repository checks             total 1h 08m");
	expect(line.length).toBe(52);

	const narrow = formatActivityLine("Reviewing an intentionally long final diff", "12m", 28, "⠹");
	expect(narrow).toBe("⠹ Reviewing an in… total 12m");
	expect(narrow.length).toBe(28);
});

test("runs derive activity locally and replace the generic working row", async () => {
	const handlers = new Map<string, (event: any, ctx: any) => Promise<void>>();
	let registeredTool = false;
	const pi = {
		on: (name: string, handler: (event: any, ctx: any) => Promise<void>) => handlers.set(name, handler),
		registerTool: () => {
			registeredTool = true;
		},
		exec: async () => ({ code: 1, stdout: "" }),
	};
	activityTitle(pi as any);

	let widgetFactory: any;
	const workingVisibility: boolean[] = [];
	const ctx = {
		cwd: "/tmp/project",
		sessionManager: {
			getEntries: () => [],
			getSessionName: () => "activity test",
		},
		ui: {
			setTitle: () => {},
			setWorkingVisible: (visible: boolean) => workingVisibility.push(visible),
			setWidget: (_key: string, content: any) => {
				widgetFactory = content;
			},
		},
	};

	expect(registeredTool).toBe(false);
	await handlers.get("before_agent_start")?.({ prompt: "Build useful activity visibility" }, ctx);
	await handlers.get("agent_start")?.({}, ctx);

	const component = widgetFactory(
		{ requestRender: () => {} },
		{ fg: (_color: string, value: string) => value },
	);
	expect(component.render(52)[0]).toBe("⠋ Working on Build useful activity visibil… total 0m");

	await handlers.get("tool_execution_start")?.({ toolCallId: "read-1", toolName: "read" }, ctx);
	const toolActivity = component.render(52)[0];
	expect(toolActivity.startsWith("⠋ Using read")).toBe(true);
	expect(toolActivity.endsWith("total 0m")).toBe(true);
	expect(toolActivity.length).toBe(52);

	await handlers.get("tool_execution_end")?.({ toolCallId: "read-1" }, ctx);
	expect(component.render(52)[0]).toBe("⠋ Working on Build useful activity visibil… total 0m");
	expect(workingVisibility).toEqual([false]);

	await handlers.get("agent_settled")?.({}, ctx);
	expect(workingVisibility).toEqual([false, true]);
});
