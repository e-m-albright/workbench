import { constants } from "node:fs";
import { access, copyFile, lstat, mkdir, realpath, rename, stat } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve } from "node:path";
import { StringEnum } from "@earendil-works/pi-ai";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import * as CodingAgent from "@earendil-works/pi-coding-agent";
import { Type, type Static } from "typebox";

const workspaceFilesSchema = Type.Object({
	action: StringEnum(["rename", "copy", "mkdir"] as const, {
		description: "Filesystem operation to perform. Deletion and overwriting are intentionally unsupported.",
	}),
	source: Type.Optional(Type.String({ description: "Existing workspace-relative source path." })),
	target: Type.String({ description: "Workspace-relative destination or directory path." }),
});

export type WorkspaceFileOperation = Static<typeof workspaceFilesSchema>;

function inside(root: string, candidate: string): boolean {
	const path = relative(root, candidate);
	return path === "" || (!path.startsWith("..") && !isAbsolute(path));
}

function requireInside(root: string, candidate: string, label: string): void {
	if (!inside(root, candidate)) throw new Error(`${label} is outside the workspace: ${candidate}`);
}

async function exists(path: string): Promise<boolean> {
	try {
		await lstat(path);
		return true;
	} catch (error) {
		if ((error as { code?: string }).code === "ENOENT") return false;
		throw error;
	}
}

async function validatedRoot(root: string): Promise<string> {
	return realpath(resolve(root));
}

async function validatedSource(root: string, source: string | undefined): Promise<string> {
	if (!source) throw new Error("source is required for rename and copy");
	const lexical = resolve(root, source.replace(/^@/, ""));
	requireInside(root, lexical, "source");
	const canonical = await realpath(lexical);
	requireInside(root, canonical, "source");
	return lexical;
}

async function validatedTarget(root: string, target: string, recursive: boolean): Promise<string> {
	const lexical = resolve(root, target.replace(/^@/, ""));
	requireInside(root, lexical, "target");
	if (await exists(lexical)) throw new Error(`target already exists: ${target}`);

	let ancestor = dirname(lexical);
	while (!(await exists(ancestor))) {
		if (!recursive) throw new Error(`target parent does not exist: ${dirname(target)}`);
		const parent = dirname(ancestor);
		if (parent === ancestor) break;
		ancestor = parent;
	}
	const canonicalAncestor = await realpath(ancestor);
	requireInside(root, canonicalAncestor, "target parent");
	return lexical;
}

export async function performWorkspaceFileOperation(
	workspaceRoot: string,
	operation: WorkspaceFileOperation,
): Promise<{ action: WorkspaceFileOperation["action"]; source?: string; target: string }> {
	const root = await validatedRoot(workspaceRoot);
	if (operation.action === "mkdir") {
		const candidate = resolve(root, operation.target.replace(/^@/, ""));
		requireInside(root, candidate, "target");
		if (await exists(candidate)) {
			const canonical = await realpath(candidate);
			requireInside(root, canonical, "target");
			if (!(await stat(candidate)).isDirectory()) {
				throw new Error(`target already exists and is not a directory: ${operation.target}`);
			}
			return { action: operation.action, target: candidate };
		}
		const target = await validatedTarget(root, operation.target, true);
		await mkdir(target, { recursive: true });
		return { action: operation.action, target };
	}

	const source = await validatedSource(root, operation.source);
	const target = await validatedTarget(root, operation.target, false);
	if (operation.action === "copy") {
		const sourceStat = await stat(source);
		if (!sourceStat.isFile()) throw new Error("copy supports regular files only");
		await copyFile(source, target, constants.COPYFILE_EXCL);
	} else {
		await rename(source, target);
	}
	return { action: operation.action, source, target };
}

async function repositoryRoot(pi: ExtensionAPI, ctx: ExtensionContext): Promise<string> {
	const result = await pi.exec("git", ["rev-parse", "--show-toplevel"], {
		cwd: ctx.cwd,
		timeout: 5000,
	});
	return result.code === 0 && result.stdout.trim() ? result.stdout.trim() : ctx.cwd;
}

async function withMutationQueues<T>(paths: string[], mutate: () => Promise<T>): Promise<T> {
	const ordered = [...new Set(paths)].sort();
	const queue = CodingAgent.withFileMutationQueue;
	const visit = (index: number): Promise<T> => {
		const path = ordered[index];
		if (!path) return mutate();
		// Some unit tests replace the Pi package with a deliberately minimal mock.
		// Production Pi always provides the shared mutation queue.
		return queue ? queue(path, () => visit(index + 1)) : visit(index + 1);
	};
	return visit(0);
}

export default function workspaceFilesExtension(pi: ExtensionAPI) {
	pi.registerTool({
		name: "workspace_files",
		label: "Workspace Files",
		description:
			"Safely rename or copy one workspace path, or create a directory. Paths must remain inside the current Git workspace. Existing destinations are never overwritten; deletion is unsupported.",
		promptSnippet: "Rename/copy workspace files or create directories without shell filesystem commands",
		promptGuidelines: [
			"Use workspace_files instead of bash mv, cp, git mv, or mkdir. It never overwrites or deletes paths.",
		],
		parameters: workspaceFilesSchema,
		async execute(_toolCallId, operation, _signal, _onUpdate, ctx) {
			const root = await repositoryRoot(pi, ctx);
			const source = operation.source ? resolve(root, operation.source.replace(/^@/, "")) : undefined;
			const target = resolve(root, operation.target.replace(/^@/, ""));
			const result = await withMutationQueues(
				[source, target].filter((path): path is string => Boolean(path)),
				() => performWorkspaceFileOperation(root, operation),
			);
			const sourceText = operation.source ? ` ${operation.source} to` : "";
			return {
				content: [
					{
						type: "text",
						text: `${operation.action}${sourceText} ${operation.target}`,
					},
				],
				details: result,
			};
		},
	});
}
