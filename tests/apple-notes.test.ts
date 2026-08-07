import { describe, expect, test } from "bun:test";
import { assertWriteAuthorized, composeNoteHtml, escapeHtml, textToHtml } from "../bin/apple-notes";

describe("Apple Notes shared CLI", () => {
	test("escapes note content before rendering HTML", () => {
		expect(escapeHtml('<script>alert("x")</script>')).toBe(
			"&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;",
		);
	});

	test("renders headings and checklist-like text as compact ordinary lists", () => {
		expect(textToHtml("START HERE\n\n☐ Check coverage\n\n☐ Submit claim")).toBe(
			"<div><h2>START HERE</h2></div><div><br></div><ul><li>Check coverage</li><li>Submit claim</li></ul>",
		);
	});

	test("composes one native-sized title instead of duplicating it in the body", () => {
		expect(composeNoteHtml("Nicole’s Benefits", "START HERE\n- Review coverage")).toBe(
			"<div><h1>Nicole’s Benefits</h1></div><div><br></div><div><h2>START HERE</h2></div><ul><li>Review coverage</li></ul>",
		);
	});

	test("requires an explicit write acknowledgement", () => {
		expect(() => assertWriteAuthorized(["create"])).toThrow("restricted to Agents");
		expect(() => assertWriteAuthorized(["create", "--confirm-write"])).not.toThrow();
	});
});
