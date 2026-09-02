import { describe, expect, test } from "bun:test";
import closeoutGovernor, {
	CLOSEOUT_INSTRUCTIONS,
	hasCloseoutSummary,
	isVerificationCommand,
} from "../agents/pi/extensions/closeout-governor";

interface Harness {
	handlers: Map<string, (event: any, ctx: any) => Promise<any> | any>;
	sent: Array<{ message: any; options: any }>;
	ctx: any;
	setAssistant(text: string, stopReason?: string): void;
}

function harness(): Harness {
	const handlers = new Map<string, (event: any, ctx: any) => Promise<any> | any>();
	const sent: Array<{ message: any; options: any }> = [];
	let assistant = {
		role: "assistant",
		content: [{ type: "text", text: "Implemented the change." }],
		stopReason: "stop",
	};
	const ctx = {
		sessionManager: {
			getBranch: () => [{ type: "message", message: assistant }],
		},
	};
	closeoutGovernor({
		on(event: string, handler: (event: any, ctx: any) => Promise<any> | any) {
			handlers.set(event, handler);
		},
		sendMessage(message: any, options: any) {
			sent.push({ message, options });
		},
	} as never);
	return {
		handlers,
		sent,
		ctx,
		setAssistant(text: string, stopReason = "stop") {
			assistant = { role: "assistant", content: [{ type: "text", text }], stopReason };
		},
	};
}

describe("Pi closeout governor", () => {
	test("recognizes verification commands and complete final status", () => {
		expect(isVerificationCommand("just check")).toBe(true);
		expect(isVerificationCommand("corepack pnpm test:e2e")).toBe(true);
		expect(isVerificationCommand("git status --short")).toBe(false);
		expect(hasCloseoutSummary("Verification: just check passed. Remaining work: none.")).toBe(true);
		expect(hasCloseoutSummary("Implemented the feature.")).toBe(false);
	});

	test("injects the closeout contract into every agent turn", async () => {
		const h = harness();
		const result = await h.handlers.get("before_agent_start")?.({ systemPrompt: "base prompt" }, h.ctx);
		expect(result.systemPrompt).toContain("base prompt");
		expect(result.systemPrompt).toContain(CLOSEOUT_INSTRUCTIONS);
	});

	test("queues one automatic follow-up when changed work settles without verification", async () => {
		const h = harness();
		await h.handlers.get("input")?.({ source: "interactive" }, h.ctx);
		await h.handlers.get("tool_execution_start")?.(
			{ toolCallId: "edit-1", toolName: "edit", args: { path: "src/index.ts" } },
			h.ctx,
		);
		await h.handlers.get("tool_execution_end")?.(
			{ toolCallId: "edit-1", toolName: "edit", isError: false },
			h.ctx,
		);
		await h.handlers.get("agent_settled")?.({}, h.ctx);
		expect(h.sent).toHaveLength(1);
		expect(h.sent[0]?.message.content).toContain("verification after the last mutation is missing");
		expect(h.sent[0]?.options).toEqual({ deliverAs: "followUp", triggerTurn: true });

		await h.handlers.get("agent_settled")?.({}, h.ctx);
		expect(h.sent).toHaveLength(1);
	});

	test("does not follow up after verification and an explicit remaining-work statement", async () => {
		const h = harness();
		await h.handlers.get("input")?.({ source: "interactive" }, h.ctx);
		await h.handlers.get("tool_execution_start")?.(
			{ toolCallId: "write-1", toolName: "write", args: { path: "src/index.ts" } },
			h.ctx,
		);
		await h.handlers.get("tool_execution_end")?.(
			{ toolCallId: "write-1", toolName: "write", isError: false },
			h.ctx,
		);
		await h.handlers.get("tool_execution_start")?.(
			{ toolCallId: "bash-1", toolName: "bash", args: { command: "just check" } },
			h.ctx,
		);
		await h.handlers.get("tool_execution_end")?.(
			{ toolCallId: "bash-1", toolName: "bash", isError: false },
			h.ctx,
		);
		h.setAssistant("Verification: `just check` passed. Remaining work: none.");
		await h.handlers.get("agent_settled")?.({}, h.ctx);
		expect(h.sent).toHaveLength(0);
	});

	test("does not auto-continue an aborted response", async () => {
		const h = harness();
		await h.handlers.get("tool_execution_start")?.(
			{ toolCallId: "edit-aborted", toolName: "edit", args: { path: "src/index.ts" } },
			h.ctx,
		);
		await h.handlers.get("tool_execution_end")?.(
			{ toolCallId: "edit-aborted", toolName: "edit", isError: false },
			h.ctx,
		);
		h.setAssistant("Stopped.", "aborted");
		await h.handlers.get("agent_settled")?.({}, h.ctx);
		expect(h.sent).toHaveLength(0);
	});
});
