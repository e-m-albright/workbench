import { realpathSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { resolve } from "node:path";
import type { ExtensionAPI, ExtensionCommandContext } from "@earendil-works/pi-coding-agent";

type SessionForker = {
	forkFrom(source: string, target: string): { getSessionFile(): string | undefined };
};

export function resolveDirectory(input: string, cwd: string): string {
	const requested = stripMatchingQuotes(input.trim());
	if (!requested || requested === "~") return homedir();

	const expanded = requested.startsWith("~/")
		? resolve(homedir(), requested.slice(2))
		: resolve(cwd, requested);
	const target = realpathSync(expanded);
	if (!statSync(target).isDirectory()) throw new Error(`Not a directory: ${target}`);
	return target;
}

export function splitZoxideQuery(input: string): string[] {
	return input.trim().split(/\s+/).filter(Boolean);
}

function stripMatchingQuotes(value: string): string {
	if (value.length < 2) return value;
	const first = value[0];
	const last = value.at(-1);
	return (first === '"' && last === '"') || (first === "'" && last === "'") ? value.slice(1, -1) : value;
}

function errorMessage(error: unknown): string {
	return error instanceof Error ? error.message : String(error);
}

export default function changeDirectoryExtension(pi: ExtensionAPI, sessions?: SessionForker) {
	async function switchDirectory(targetCwd: string, ctx: ExtensionCommandContext): Promise<void> {
		const currentCwd = realpathSync(ctx.cwd);
		if (targetCwd === currentCwd) {
			ctx.ui.notify(`Already in ${targetCwd}`, "info");
			return;
		}

		const sourceSession = ctx.sessionManager.getSessionFile();
		if (!sourceSession) {
			ctx.ui.notify("The current session is not persisted, so its conversation cannot be moved", "error");
			return;
		}

		let targetSession: string | undefined;
		try {
			const sessionFactory = sessions ?? (await import("@earendil-works/pi-coding-agent")).SessionManager;
			targetSession = sessionFactory.forkFrom(sourceSession, targetCwd).getSessionFile();
		} catch (error) {
			ctx.ui.notify(`Could not switch projects: ${errorMessage(error)}`, "error");
			return;
		}
		if (!targetSession) {
			ctx.ui.notify("Could not create a session in the target directory", "error");
			return;
		}

		const result = await ctx.switchSession(targetSession, {
			withSession: async (nextCtx) => {
				nextCtx.ui.notify(`Working directory: ${nextCtx.cwd}`, "info");
			},
		});
		if (result.cancelled) ctx.ui.notify("Project switch cancelled", "warning");
	}

	pi.registerCommand("z", {
		description: "Jump to a zoxide directory while preserving this conversation",
		handler: async (args, ctx) => {
			await ctx.waitForIdle();
			let query = args.trim();
			if (!query) {
				query = (await ctx.ui.input("Jump to directory:", "zoxide query"))?.trim() ?? "";
				if (!query) return;
			}

			const result = await pi.exec("zoxide", ["query", "--exclude", ctx.cwd, ...splitZoxideQuery(query)], {
				timeout: 5_000,
			});
			if (result.code !== 0 || !result.stdout.trim()) {
				ctx.ui.notify(`z: no directory matched "${query}"`, "warning");
				return;
			}

			try {
				await switchDirectory(resolveDirectory(result.stdout.trim(), ctx.cwd), ctx);
			} catch (error) {
				ctx.ui.notify(`z: ${errorMessage(error)}`, "error");
			}
		},
	});

	pi.registerCommand("cd", {
		description: "Switch to an explicit directory while preserving this conversation",
		handler: async (args, ctx) => {
			await ctx.waitForIdle();
			try {
				await switchDirectory(resolveDirectory(args, ctx.cwd), ctx);
			} catch (error) {
				ctx.ui.notify(`cd: ${errorMessage(error)}`, "error");
			}
		},
	});
}
