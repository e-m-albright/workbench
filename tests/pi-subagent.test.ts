import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, test, vi } from "vitest";

const { examples } = vi.hoisted(() => ({ examples: { path: "" } }));
vi.mock("@earendil-works/pi-coding-agent", () => ({ getExamplesPath: () => examples.path }));

import subagent from "../agents/pi/extensions/subagent";

test("loads the installed upstream example without owning its implementation", async () => {
	examples.path = mkdtempSync(join(tmpdir(), "pi-upstream-subagent-"));
	const directory = join(examples.path, "extensions/subagent");
	mkdirSync(directory, { recursive: true });
	writeFileSync(
		join(directory, "index.ts"),
		'export default function (pi) { pi.registerTool({ name: "subagent" }); }',
	);
	const registerTool = vi.fn();
	await subagent({ registerTool } as any);
	expect(registerTool).toHaveBeenCalledWith({ name: "subagent" });
});

test("keeps worktree isolation and nonrecursive delegation in the agent definition", () => {
	const agent = readFileSync(new URL("../agents/pi/agents/implementer.md", import.meta.url), "utf8");
	expect(agent).toContain("worktree");
	expect(agent).toContain("Do not delegate");
	expect(agent).toContain("tools: read,grep,find,ls,bash,edit,write,workspace_files");
	expect(agent).not.toMatch(/^model:/m);
});
