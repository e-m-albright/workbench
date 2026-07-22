import { describe, expect, mock, test } from "bun:test";

mock.module("@earendil-works/pi-coding-agent", () => ({ getAgentDir: () => "/tmp/pi-agent" }));
// typebox is a virtual module provided by Pi's extension loader at runtime.
mock.module("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Number: schema, Optional: schema } };
});
const { buildEventsUrl, capText, extractPlainText, headerValue } = await import(
	"../agents/pi/extensions/google-readonly"
);

function b64url(text: string): string {
	return Buffer.from(text, "utf8").toString("base64url");
}

describe("Pi Google read-only connector", () => {
	test("extracts the first text/plain body from a nested payload", () => {
		const payload = {
			mimeType: "multipart/alternative",
			parts: [
				{ mimeType: "text/html", body: { data: b64url("<b>html</b>") } },
				{
					mimeType: "multipart/mixed",
					parts: [{ mimeType: "text/plain", body: { data: b64url("plain body") } }],
				},
			],
		};
		expect(extractPlainText(payload)).toBe("plain body");
		expect(extractPlainText(undefined)).toBe("");
	});

	test("caps long bodies with an explicit truncation marker", () => {
		const long = "x".repeat(5000);
		const capped = capText(long, 100);
		expect(capped.length).toBeLessThan(200);
		expect(capped).toContain("truncated (5000 chars total)");
		expect(capText("short")).toBe("short");
	});

	test("reads headers case-insensitively", () => {
		const headers = [{ name: "SUBJECT", value: "hello" }];
		expect(headerValue(headers, "Subject")).toBe("hello");
		expect(headerValue(undefined, "Subject")).toBe("");
	});

	test("builds calendar event URLs only against googleapis.com", () => {
		const url = buildEventsUrl({
			calendarId: "team@example.com",
			timeMin: "2026-07-21T00:00:00Z",
			query: "standup",
			maxResults: 10,
		});
		expect(url.startsWith("https://www.googleapis.com/calendar/v3/calendars/team%40example.com/events")).toBe(
			true,
		);
		expect(url).toContain("singleEvents=true");
		expect(url).toContain("q=standup");
		expect(url).not.toContain("timeMax");
	});
});
