import { lstat, mkdir, realpath, rename } from "node:fs/promises";
import { basename, isAbsolute, relative, resolve } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const schema = Type.Object({
	path: Type.String({ description: "A file under ~/code/ingress to move to the macOS Trash." }),
});

function inside(root: string, candidate: string): boolean {
	const path = relative(root, candidate);
	return path === "" || (!path.startsWith("..") && !isAbsolute(path));
}

export default function ingressExtension(pi: ExtensionAPI) {
	pi.registerTool({
		name: "ingress_discard",
		label: "Discard ingress file",
		description:
			"Move one file from ~/code/ingress to the macOS Trash after interactive confirmation. Agent handoffs cannot be discarded through this tool.",
		promptSnippet: "Discard one consumed ingress file through a confirmed move to Trash",
		parameters: schema,
		async execute(_toolCallId, input, _signal, _onUpdate, ctx) {
			if (!ctx.hasUI) throw new Error("Ingress discard requires interactive confirmation.");
			const home = process.env.HOME;
			if (!home) throw new Error("HOME is unavailable.");
			const root = await realpath(resolve(home, "code/ingress"));
			const handoffRoots = [resolve(root, "handoffs")];
			const configured = process.env.WORKBENCH_HANDOFF_HOME;
			if (configured) handoffRoots.push(resolve(configured.replace(/^~(?=\/|$)/, home)));
			const handoffs = await Promise.all(
				handoffRoots.map(async (path) => {
					try {
						return await realpath(path);
					} catch (error) {
						if ((error as NodeJS.ErrnoException).code === "ENOENT") return path;
						throw error;
					}
				}),
			);
			const lexical = resolve(root, input.path.replace(/^@/, ""));
			if (!inside(root, lexical)) throw new Error("Ingress path escapes ~/code/ingress.");
			const source = await realpath(lexical);
			if (!inside(root, source)) throw new Error("Ingress symlink target escapes ~/code/ingress.");
			if (handoffs.some((path) => inside(path, source)))
				throw new Error("Agent handoffs use the handoff lifecycle, not ingress discard.");
			if (!(await lstat(source)).isFile()) throw new Error("Ingress discard supports regular files only.");
			if (!(await ctx.ui.confirm("Discard ingress file", `Move ${relative(root, source)} to Trash?`))) {
				throw new Error("Ingress discard cancelled by user.");
			}
			const trash = resolve(home, ".Trash");
			await mkdir(trash, { recursive: true });
			const destination = resolve(trash, `${basename(source)}.${Date.now().toString(36)}.ingress-trash`);
			await rename(source, destination);
			return {
				content: [{ type: "text", text: `Moved ${relative(root, source)} to Trash.` }],
				details: { source, destination },
			};
		},
	});
}
