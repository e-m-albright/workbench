import { describe, expect, test } from "bun:test";
import { resolveAgentDir } from "../agents/pi/extensions/lib/agent-dir";

describe("Pi agent directory", () => {
	test("honors Pi's documented override", () => {
		expect(resolveAgentDir({ PI_CODING_AGENT_DIR: "/tmp/pi-test" }, "/home/tester")).toBe("/tmp/pi-test");
	});

	test("uses Pi's documented default", () => {
		expect(resolveAgentDir({}, "/home/tester")).toBe("/home/tester/.pi/agent");
	});
});
