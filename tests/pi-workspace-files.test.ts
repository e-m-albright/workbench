import { describe, expect, mock, test } from "bun:test";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

mock.module("@earendil-works/pi-ai", () => ({
	StringEnum: (values: string[], options: Record<string, unknown>) => ({
		type: "string",
		enum: values,
		...options,
	}),
}));
mock.module("@earendil-works/pi-coding-agent", () => ({
	withFileMutationQueue: async (_path: string, mutate: () => Promise<unknown>) => mutate(),
}));
mock.module("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Optional: schema } };
});
const { performWorkspaceFileOperation } = await import("../agents/pi/extensions/workspace-files");

async function workspace(): Promise<string> {
	return mkdtemp(join(tmpdir(), "workbench-workspace-files-"));
}

describe("Pi workspace file operations", () => {
	test("renames and copies files without overwriting destinations", async () => {
		const root = await workspace();
		await writeFile(join(root, "source.txt"), "source\n");

		await performWorkspaceFileOperation(root, {
			action: "copy",
			source: "source.txt",
			target: "copy.txt",
		});
		expect(await readFile(join(root, "copy.txt"), "utf8")).toBe("source\n");

		await performWorkspaceFileOperation(root, {
			action: "rename",
			source: "copy.txt",
			target: "renamed.txt",
		});
		expect(await readFile(join(root, "renamed.txt"), "utf8")).toBe("source\n");
		await expect(
			performWorkspaceFileOperation(root, {
				action: "copy",
				source: "source.txt",
				target: "renamed.txt",
			}),
		).rejects.toThrow("already exists");
	});

	test("creates directories and rejects paths outside the workspace", async () => {
		const root = await workspace();
		await performWorkspaceFileOperation(root, { action: "mkdir", target: "nested/output" });
		await performWorkspaceFileOperation(root, { action: "mkdir", target: "nested/output" });
		await writeFile(join(root, "nested/output/result.txt"), "ok\n");
		expect(await readFile(join(root, "nested/output/result.txt"), "utf8")).toBe("ok\n");

		await expect(
			performWorkspaceFileOperation(root, { action: "mkdir", target: "../escape" }),
		).rejects.toThrow("outside the workspace");
	});

	test("does not copy directories through the file-copy action", async () => {
		const root = await workspace();
		await performWorkspaceFileOperation(root, { action: "mkdir", target: "directory" });
		await expect(
			performWorkspaceFileOperation(root, {
				action: "copy",
				source: "directory",
				target: "directory-copy",
			}),
		).rejects.toThrow("regular files");
	});
});
