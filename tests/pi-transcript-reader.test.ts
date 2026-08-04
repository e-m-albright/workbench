import { expect, test } from "bun:test";
import {
	clampScrollOffset,
	classifyReaderInput,
	formatWorkSummary,
	parseTranscript,
	reconcileReaderSelection,
	selectLatestReadableTurn,
} from "../agents/pi/extensions/transcript-reader";

function message(id: string, role: string, content: unknown, extras: Record<string, unknown> = {}) {
	return {
		type: "message" as const,
		id,
		parentId: null,
		timestamp: "2026-08-01T00:00:00.000Z",
		message: { role, content, timestamp: Date.now(), ...extras },
	};
}

test("groups each prompt with compact work and its final answer", () => {
	const turns = parseTranscript([
		message("u1", "user", "Investigate the adapter and recommend a fix."),
		message(
			"a1",
			"assistant",
			[
				{ type: "text", text: "I’ll inspect the implementation first." },
				{ type: "toolCall", id: "call-1", name: "read", arguments: { path: "adapter.ts" } },
			],
			{ stopReason: "toolUse" },
		),
		message("r1", "toolResult", [{ type: "text", text: "file contents" }], {
			toolCallId: "call-1",
			toolName: "read",
			isError: false,
		}),
		message(
			"a2",
			"assistant",
			[{ type: "text", text: "## Recommendation\n\nFix the adapter boundary." }],
			{ stopReason: "stop" },
		),
		message("u2", "user", [{ type: "text", text: "What should I test?" }]),
	]);

	expect(turns).toHaveLength(2);
	expect(turns[0]?.prompt).toBe("Investigate the adapter and recommend a fix.");
	expect(turns[0]?.answer).toBe("## Recommendation\n\nFix the adapter boundary.");
	expect(turns[0]?.work.notes).toEqual(["I’ll inspect the implementation first."]);
	expect(turns[0]?.work.tools).toEqual({ read: 1 });
	expect(turns[1]?.prompt).toBe("What should I test?");
	expect(turns[1]?.answer).toBeUndefined();
});

test("summarizes work without exposing tool output", () => {
	expect(formatWorkSummary({ notes: [], tools: {}, errors: 0 })).toBe("No separate work steps");
	expect(formatWorkSummary({ notes: ["Checking"], tools: { read: 4, edit: 2, bash: 1 }, errors: 1 })).toBe(
		"7 tools · 4 read · 2 edit · 1 bash · 1 error",
	);
});

test("delegates legacy and Kitty-protocol escape recognition to Pi's key matcher", () => {
	const escapeInputs = new Set(["\u001b", "\u001b[27u", "\u001b[27;1u"]);
	const matchesKey = (data: string, key: string) => key === "escape" && escapeInputs.has(data);
	expect(classifyReaderInput("\u001b", matchesKey)).toBe("close");
	expect(classifyReaderInput("\u001b[27u", matchesKey)).toBe("close");
	expect(classifyReaderInput("\u001b[27;1u", matchesKey)).toBe("close");
});

test("allows an answer landmark to sit at the top even when the turn is shorter than the viewport", () => {
	expect(clampScrollOffset(8, 20, 5)).toBe(5);
	expect(clampScrollOffset(8, 20, 99)).toBe(7);
	expect(clampScrollOffset(0, 20, 5)).toBe(0);
});

test("a live reader follows the current turn and jumps when its final answer arrives", () => {
	const before = [
		{ prompt: "done", work: { notes: [], tools: {}, errors: 0 }, answer: "old answer" },
		{ prompt: "active", work: { notes: [], tools: {}, errors: 0 } },
	];
	const after = [before[0]!, { ...before[1]!, answer: "new final" }];
	expect(reconcileReaderSelection(before, after, 1, true)).toEqual({ turnIndex: 1, anchor: "answer" });
	expect(reconcileReaderSelection(before, after, 0, false)).toEqual({ turnIndex: 0 });
});

test("opens on the newest completed answer and falls back to the newest prompt", () => {
	const completed = { prompt: "done", work: { notes: [], tools: {}, errors: 0 }, answer: "answer" };
	const pending = { prompt: "pending", work: { notes: [], tools: {}, errors: 0 } };

	expect(selectLatestReadableTurn([completed, pending])).toBe(0);
	expect(selectLatestReadableTurn([pending])).toBe(0);
	expect(selectLatestReadableTurn([])).toBe(-1);
});

test("counts failed tool results and ignores messages before the first prompt", () => {
	const turns = parseTranscript([
		message("orphan", "assistant", [{ type: "text", text: "orphan" }], { stopReason: "stop" }),
		message("u1", "user", "Run the check."),
		message(
			"a1",
			"assistant",
			[{ type: "toolCall", id: "call-1", name: "bash", arguments: { command: "just check" } }],
			{ stopReason: "toolUse" },
		),
		message("r1", "toolResult", [{ type: "text", text: "failed" }], {
			toolCallId: "call-1",
			toolName: "bash",
			isError: true,
		}),
	]);

	expect(turns).toHaveLength(1);
	expect(turns[0]?.work.tools).toEqual({ bash: 1 });
	expect(turns[0]?.work.errors).toBe(1);
});
