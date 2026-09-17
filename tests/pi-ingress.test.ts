import { afterEach, beforeEach, expect, mock, test } from "bun:test";
import { access, mkdir, mkdtemp, readFile, realpath, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

mock.module("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Optional: schema } };
});
const { default: ingressExtension } = await import("../agents/pi/extensions/ingress");

let home: string;
let priorHome: string | undefined;
let priorHandoff: string | undefined;
let execute: (...args: any[]) => Promise<any>;
let confirmations: number;
const context = { hasUI: true, ui: { confirm: async () => (++confirmations, true) } };

beforeEach(async () => {
	home = await realpath(await mkdtemp(join(tmpdir(), "workbench-ingress-")));
	priorHome = process.env.HOME;
	priorHandoff = process.env.WORKBENCH_HANDOFF_HOME;
	process.env.HOME = home;
	delete process.env.WORKBENCH_HANDOFF_HOME;
	await mkdir(join(home, "code/ingress"), { recursive: true });
	confirmations = 0;
	ingressExtension({ registerTool: (tool: any) => (execute = tool.execute) } as never);
});
afterEach(async () => {
	if (priorHome === undefined) delete process.env.HOME;
	else process.env.HOME = priorHome;
	if (priorHandoff === undefined) delete process.env.WORKBENCH_HANDOFF_HOME;
	else process.env.WORKBENCH_HANDOFF_HOME = priorHandoff;
	await rm(home, { recursive: true, force: true });
});

for (const override of [undefined, "~/code/ingress/custom-handoffs"]) {
	test(`protects the ${override ? "configured" : "default"} handoff queue before confirmation`, async () => {
		if (override) process.env.WORKBENCH_HANDOFF_HOME = override;
		const folder = override ? "custom-handoffs" : "handoffs";
		const path = join(home, "code/ingress", folder, "ready/task.md");
		await mkdir(join(path, ".."), { recursive: true });
		await writeFile(path, "keep this handoff");
		await expect(execute("id", { path }, undefined, undefined, context)).rejects.toThrow("handoff lifecycle");
		expect(await readFile(path, "utf8")).toBe("keep this handoff");
		expect(confirmations).toBe(0);
	});
}

test("protects a configured handoff queue reached through a symlink", async () => {
	const target = join(home, "code/ingress/actual-handoffs");
	await mkdir(target);
	await writeFile(join(target, "task.md"), "keep this handoff");
	await symlink(target, join(home, "handoff-link"));
	process.env.WORKBENCH_HANDOFF_HOME = "~/handoff-link";
	await expect(
		execute("id", { path: join(target, "task.md") }, undefined, undefined, context),
	).rejects.toThrow("handoff lifecycle");
	expect(confirmations).toBe(0);
});

test("still moves an ordinary confirmed ingress file to Trash", async () => {
	const path = join(home, "code/ingress/source.txt");
	await writeFile(path, "consumed source");
	const result = await execute("id", { path }, undefined, undefined, context);
	expect(await readFile(result.details.destination, "utf8")).toBe("consumed source");
	await expect(access(path)).rejects.toThrow();
	expect(confirmations).toBe(1);
});
