import { describe, expect, test } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Pi welcome header", () => {
	test("prints the authoritative installed Pi version and managed marker", () => {
		const path = resolve(import.meta.dirname, "../agents/pi/extensions/welcome.ts");
		const source = readFileSync(path, "utf8");
		expect(source).toContain("type ExtensionAPI, VERSION");
		expect(source).toContain("return `Pi ${version} · Workbench managed`");
		expect(source).toContain("welcomeLabel(VERSION)");
	});
});
