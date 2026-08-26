import { describe, expect, mock, test } from "bun:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

mock.module("@earendil-works/pi-coding-agent", () => ({}));
const { classifyCommand } = await import("../agents/pi/extensions/safe-git");

interface Vector {
	command: string;
	hook: "block" | "allow";
	safeGit: "high" | "medium" | null;
}

const vectors: Vector[] = JSON.parse(
	readFileSync(resolve(import.meta.dir, "data/git-guard-vectors.json"), "utf8"),
).vectors;

describe("safe-git command classification", () => {
	test("shared guard vectors classify at the expected severity", () => {
		for (const { command, safeGit } of vectors) {
			const match = classifyCommand(command);
			if (safeGit === null) {
				expect(match, command).toBeNull();
			} else {
				expect(match, command).not.toBeNull();
				expect(match?.severity, command).toBe(safeGit);
			}
		}
	});

	test("first match wins: a force push classifies as force push, not plain push", () => {
		expect(classifyCommand("git push --force origin main")?.action).toBe("force push");
		expect(classifyCommand("git push origin +main")?.action).toBe("force push");
		expect(classifyCommand("git push origin main")?.action).toBe("push");
	});

	test("gh reads pass silently so session approvals never cover unseen mutations", () => {
		expect(classifyCommand("gh pr view 12")).toBeNull();
		expect(classifyCommand("gh run list")).toBeNull();
		expect(classifyCommand("gh pr merge 12")?.action).toBe("mutating GitHub CLI");
	});
});
