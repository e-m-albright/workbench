import { afterEach, describe, expect, test, vi } from "vitest";

vi.doMock("@earendil-works/pi-coding-agent", () => ({ VERSION: "test-version" }));
vi.doMock("@earendil-works/pi-tui", () => ({ truncateToWidth: (text: string) => text }));
const { default: welcome, welcomeLabel } = await import("../agents/pi/extensions/welcome");
afterEach(() => vi.unstubAllEnvs());

describe("Pi welcome header", () => {
	test("names configuration without implying native containment", () => {
		vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", undefined);
		vi.stubEnv("WORKBENCH_PI_MODE", undefined);
		expect(welcomeLabel("0.85.1")).toBe("Pi 0.85.1 · Workbench configuration · native");
	});
	test("names managed authority when installed inside the outer sandbox", () => {
		vi.stubEnv("WORKBENCH_AGENT_AUTHORITY", "managed");
		expect(welcomeLabel("0.85.1")).toBe("Pi 0.85.1 · Workbench configuration · managed");
	});
	test("renders the installed version", async () => {
		let sessionStart: any;
		let header: any;
		welcome({
			on: (_event: string, handler: any) => {
				sessionStart = handler;
			},
		} as any);
		await sessionStart(
			{},
			{
				hasUI: true,
				ui: {
					setHeader: (factory: any) => {
						header = factory();
					},
				},
			},
		);
		expect(header.render(120).at(-1)).toContain("Pi test-version");
	});
});
