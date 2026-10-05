import { describe, expect, test, vi } from "vitest";

vi.mock("typebox", () => ({ Type: { Object: vi.fn(), String: vi.fn() } }));
vi.mock("@earendil-works/pi-coding-agent", () => ({}));

const { osc52Sequence } = await import("../agents/pi/extensions/clipboard");

describe("Pi clipboard", () => {
	test("encodes paste-ready text through the one-way OSC 52 channel", () => {
		const sequence = osc52Sequence("Hello\n\nWorld");
		expect(sequence).toBe(`\u001b]52;c;${Buffer.from("Hello\n\nWorld").toString("base64")}\u0007`);
		expect(sequence).not.toContain("Hello");
	});
});
