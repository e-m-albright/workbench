import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

export const CLOSEOUT_INSTRUCTIONS = `Closeout contract for implementation work:
- After the last file mutation, run the narrowest appropriate verification. A successful readback is enough for prose-only changes; code needs the relevant test, type, lint, or build check.
- Do not make the user ask whether the work is finished. Before settling, state verification evidence and explicitly state any remaining, deferred, blocked, or skipped work. Say that nothing remains when that is true.
- If verification fails, continue fixing the root cause unless it is unrelated or requires user authority; then report the exact blocker.`;

interface TurnState {
	mutations: number;
	mutatedPaths: Set<string>;
	verifiedAfterMutation: boolean;
	verificationEvidence: string[];
	followUpQueued: boolean;
}

function newTurnState(): TurnState {
	return {
		mutations: 0,
		mutatedPaths: new Set(),
		verifiedAfterMutation: false,
		verificationEvidence: [],
		followUpQueued: false,
	};
}

function assistantText(message: any): string {
	if (!message || message.role !== "assistant" || !Array.isArray(message.content)) return "";
	return message.content
		.filter((block: any) => block?.type === "text" && typeof block.text === "string")
		.map((block: any) => block.text)
		.join("\n")
		.trim();
}

function latestAssistant(ctx: ExtensionContext): any | undefined {
	const entries = ctx.sessionManager.getBranch();
	for (let index = entries.length - 1; index >= 0; index--) {
		const entry = entries[index];
		if (entry?.type === "message" && entry.message.role === "assistant") return entry.message;
	}
	return undefined;
}

function toolPath(args: unknown): string | undefined {
	if (!args || typeof args !== "object") return undefined;
	const record = args as Record<string, unknown>;
	for (const key of ["path", "target"] as const) {
		if (typeof record[key] === "string") return record[key];
	}
	return undefined;
}

export function isVerificationCommand(command: string): boolean {
	return (
		/\bjust\s+(?:check|ci|test|lint|typecheck|build|verify|health|web-check|web-test)\b/i.test(command) ||
		/\b(?:pytest|pyright|ruff|vitest|playwright)\b/i.test(command) ||
		/\b(?:bun|npm|pnpm|yarn)\s+(?:run\s+)?(?:test|check|lint|build|typecheck)\b/i.test(command)
	);
}

export function hasCloseoutSummary(text: string): boolean {
	const verification = /\b(?:verification|verified|tests?|checks?|build|lint)\b/i.test(text);
	const remaining =
		/\b(?:remaining|deferred|blocked|skipped|unfinished|nothing remains|no (?:known )?(?:work|items?) remain)\b/i.test(
			text,
		);
	return verification && remaining;
}

function verificationForRead(state: TurnState, args: unknown): string | undefined {
	const path = toolPath(args);
	if (!path || !state.mutatedPaths.has(path)) return undefined;
	return `read ${path}`;
}

export default function closeoutGovernor(pi: ExtensionAPI) {
	let state = newTurnState();
	const toolArguments = new Map<string, unknown>();

	pi.on("session_start", async () => {
		state = newTurnState();
	});

	pi.on("input", async (event) => {
		if (event.source !== "extension") state = newTurnState();
	});

	pi.on("before_agent_start", async (event) => ({
		systemPrompt: `${event.systemPrompt}\n\n${CLOSEOUT_INSTRUCTIONS}`,
	}));

	pi.on("tool_execution_start", async (event) => {
		toolArguments.set(event.toolCallId, event.args);
	});

	pi.on("tool_execution_end", async (event) => {
		const args = toolArguments.get(event.toolCallId);
		toolArguments.delete(event.toolCallId);
		if (event.isError) return;
		if (["edit", "write", "workspace_files"].includes(event.toolName)) {
			state.mutations += 1;
			const path = toolPath(args);
			if (path) state.mutatedPaths.add(path);
			state.verifiedAfterMutation = false;
			state.verificationEvidence = [];
			return;
		}

		let evidence: string | undefined;
		if (event.toolName === "read") evidence = verificationForRead(state, args);
		if (event.toolName === "bash") {
			const command = String((args as { command?: unknown } | undefined)?.command ?? "");
			if (isVerificationCommand(command)) evidence = command.split("\n", 1)[0];
		}
		if (state.mutations > 0 && evidence) {
			state.verifiedAfterMutation = true;
			state.verificationEvidence.push(evidence);
		}
	});

	pi.on("agent_settled", async (_event, ctx) => {
		if (state.mutations === 0 || state.followUpQueued) return;
		const assistant = latestAssistant(ctx);
		if (!assistant || assistant.stopReason !== "stop") return;
		const summaryMissing = !hasCloseoutSummary(assistantText(assistant));
		if (state.verifiedAfterMutation && !summaryMissing) return;

		state.followUpQueued = true;
		const problems = [
			...(!state.verifiedAfterMutation ? ["verification after the last mutation is missing"] : []),
			...(summaryMissing
				? ["the final answer does not explicitly state verification and remaining work"]
				: []),
		];
		pi.sendMessage(
			{
				customType: "closeout-governor",
				content: `Closeout governor: ${problems.join("; ")}. Continue autonomously now. Run the appropriate focused verification if needed, then give one concise corrected final status with verification evidence and an explicit remaining-work statement. Do not ask the user to request closeout.`,
				display: false,
				details: {
					mutations: state.mutations,
					verificationEvidence: state.verificationEvidence,
				},
			},
			{ deliverAs: "followUp", triggerTurn: true },
		);
	});
}
