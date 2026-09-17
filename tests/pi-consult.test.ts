import { expect, test } from "bun:test";
import consult from "../agents/pi/extensions/consult";

test("local sessions cannot send a consult to cloud CLIs", async () => {
	const old = process.env.WORKBENCH_PI_MODE;
	process.env.WORKBENCH_PI_MODE = "local-unrestricted";
	try {
		let command: any;
		const calls: unknown[] = [];
		const notices: string[] = [];
		consult({
			registerCommand: (_name: string, value: any) => (command = value),
			exec: (...args: unknown[]) => {
				calls.push(args);
				return Promise.resolve({ code: 0, stdout: "ok" });
			},
		} as any);
		await command.handler("review private context", {
			cwd: "/tmp/example",
			model: { provider: "omlx" },
			ui: { notify: (text: string) => notices.push(text) },
		} as any);
		expect(calls).toEqual([]);
		expect(notices.join(" ")).toContain("local");
	} finally {
		if (old === undefined) delete process.env.WORKBENCH_PI_MODE;
		else process.env.WORKBENCH_PI_MODE = old;
	}
});
