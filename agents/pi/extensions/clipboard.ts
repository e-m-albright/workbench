import { spawn } from "node:child_process";
import { Type } from "typebox";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export type ClipboardRunner = (
	command: "pbcopy" | "pbpaste",
	input?: string,
	signal?: AbortSignal,
) => Promise<string>;

async function runClipboardCommand(
	command: "pbcopy" | "pbpaste",
	input?: string,
	signal?: AbortSignal,
): Promise<string> {
	return new Promise((resolve, reject) => {
		const child = spawn(command, [], { signal, stdio: ["pipe", "pipe", "pipe"] });
		const stdout: Buffer[] = [];
		const stderr: Buffer[] = [];
		child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
		child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
		child.on("error", reject);
		child.on("close", (code) => {
			if (code === 0) {
				resolve(Buffer.concat(stdout).toString("utf8"));
				return;
			}
			reject(
				new Error(
					`${command} failed with exit code ${code}: ${Buffer.concat(stderr).toString("utf8").trim()}`,
				),
			);
		});
		child.stdin.end(input);
	});
}

export async function copyAndVerifyPlainText(
	text: string,
	run: ClipboardRunner = runClipboardCommand,
	signal?: AbortSignal,
): Promise<void> {
	await run("pbcopy", text, signal);
	const copied = await run("pbpaste", undefined, signal);
	if (copied !== text) throw new Error("Clipboard verification failed: pasted text differs from input");
}

export default function clipboardExtension(pi: ExtensionAPI) {
	pi.registerTool({
		name: "clipboard_copy",
		label: "Copy to Clipboard",
		description: "Copy approved plain text to the local macOS clipboard and verify an exact match.",
		promptSnippet: "Copy approved plain text to the local macOS clipboard with exact verification",
		promptGuidelines: [
			"Use clipboard_copy for paste-ready text the user requested. Copy only the finished deliverable, never secrets or surrounding analysis.",
		],
		parameters: Type.Object({
			text: Type.String({ minLength: 1, maxLength: 20000, description: "Approved plain text to copy." }),
		}),
		async execute(_toolCallId, params, signal) {
			if (process.platform !== "darwin") throw new Error("clipboard_copy requires macOS");
			await copyAndVerifyPlainText(params.text, runClipboardCommand, signal);
			return {
				content: [{ type: "text", text: "Copied plain text to the clipboard and verified it." }],
				details: { characters: params.text.length, verified: true },
			};
		},
	});
}
