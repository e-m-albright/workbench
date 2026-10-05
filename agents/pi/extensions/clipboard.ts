import { Type } from "typebox";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export function osc52Sequence(text: string): string {
	return `\u001b]52;c;${Buffer.from(text, "utf8").toString("base64")}\u0007`;
}

export default function clipboardExtension(pi: ExtensionAPI) {
	pi.registerTool({
		name: "clipboard_copy",
		label: "Copy to Clipboard",
		description: "Copy approved plain text through the terminal's one-way OSC 52 channel.",
		promptSnippet: "Copy approved plain text to the local macOS clipboard",
		promptGuidelines: [
			"Use clipboard_copy for paste-ready text the user requested. Copy only the finished deliverable, never secrets or surrounding analysis.",
		],
		parameters: Type.Object({
			text: Type.String({ minLength: 1, maxLength: 20000, description: "Approved plain text to copy." }),
		}),
		async execute(_toolCallId, params) {
			if (!process.stdout.isTTY) throw new Error("clipboard_copy requires an interactive terminal");
			process.stdout.write(osc52Sequence(params.text));
			return {
				content: [{ type: "text", text: "Sent plain text to the terminal clipboard." }],
				details: { characters: params.text.length },
			};
		},
	});
}
