import { mkdtempSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test, vi } from "vitest";

vi.doMock("@earendil-works/pi-coding-agent", () => ({ getAgentDir: () => "/tmp/pi-agent" }));
// typebox is a virtual module provided by Pi's extension loader at runtime.
vi.doMock("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Number: schema, Optional: schema } };
});
const {
	CONNECTOR_ROOT,
	buildEventsUrl,
	capText,
	extractPlainText,
	formatThread,
	formatThreadSearchResult,
	headerValue,
	oauthCallbackCode,
	saveTokens,
	tokenResponse,
} = await import("../agents/pi/extensions/google-readonly");

function b64url(text: string): string {
	return Buffer.from(text, "utf8").toString("base64url");
}

describe("Pi Google read-only connector", () => {
	test("owns its credential root and persists tokens privately", () => {
		expect(CONNECTOR_ROOT).toMatch(/[/\\]\.local[/\\]share[/\\]workbench[/\\]connectors$/);
		const root = mkdtempSync(join(tmpdir(), "workbench-google-token-"));
		const path = join(root, "nested", "token.json");
		try {
			const tokens = tokenResponse(
				{ access_token: "new-access", expires_in: 1200 },
				"existing-refresh",
				1000,
			);
			expect(tokens).toEqual({
				accessToken: "new-access",
				refreshToken: "existing-refresh",
				expiresAt: 1_201_000,
			});
			saveTokens(tokens, path);
			expect(JSON.parse(readFileSync(path, "utf8"))).toEqual(tokens);
			expect(statSync(join(root, "nested")).mode & 0o777).toBe(0o700);
			expect(statSync(path).mode & 0o777).toBe(0o600);
		} finally {
			rmSync(root, { recursive: true, force: true });
		}
	});

	test("accepts only the expected OAuth callback state", () => {
		expect(oauthCallbackCode(new URL("http://127.0.0.1/callback?code=ok&state=expected"), "expected")).toBe(
			"ok",
		);
		expect(() =>
			oauthCallbackCode(new URL("http://127.0.0.1/callback?code=ok&state=wrong"), "expected"),
		).toThrow("state mismatch");
		expect(() =>
			oauthCallbackCode(new URL("http://127.0.0.1/callback?error=denied&state=expected"), "expected"),
		).toThrow("denied");
	});

	test("rejects malformed token responses", () => {
		expect(() => tokenResponse({}, "refresh")).toThrow("access_token");
		expect(() => tokenResponse({ access_token: "access" })).toThrow("refresh_token");
		expect(() =>
			tokenResponse({ access_token: "access", refresh_token: "refresh", expires_in: "nope" }),
		).toThrow("expires_in");
	});

	test("bounds a whole Gmail thread, including oversized headers and omitted messages", () => {
		const messages = Array.from({ length: 100 }, () => ({
			payload: {
				mimeType: "text/plain",
				headers: [{ name: "Subject", value: "s".repeat(100_000) }],
				body: { data: b64url("x".repeat(5000)) },
			},
		}));
		const text = formatThread(messages);
		expect(text.length).toBeLessThanOrEqual(24_000);
		expect(text).toContain("truncated");
		expect(text).toContain("80 messages omitted");
		expect(formatThread([])).toBe("Empty thread.");
	});
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

	test("formats search metadata promised by the tool contract", () => {
		const line = formatThreadSearchResult({
			id: "thread-1",
			snippet: "Preview",
			messages: [
				{
					payload: {
						headers: [
							{ name: "Date", value: "Tue, 25 Aug 2026 10:00:00 -0400" },
							{ name: "From", value: "Alice <alice@example.com>" },
							{ name: "Subject", value: "Status" },
						],
					},
				},
			],
		});
		expect(line).toContain("thread-1");
		expect(line).toContain("Alice <alice@example.com>");
		expect(line).toContain("Status");
		expect(line).toContain("Preview");
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
