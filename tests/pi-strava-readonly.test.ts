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
	buildActivitiesUrl,
	formatActivity,
	formatAthleteStats,
	oauthCallbackCode,
	storeTokenResponse,
} = await import("../agents/pi/extensions/strava-readonly");

describe("Pi Strava read-only connector", () => {
	test("owns its credential root and persists rotated tokens privately", () => {
		expect(CONNECTOR_ROOT).toMatch(/[/\\]\.local[/\\]share[/\\]workbench[/\\]connectors$/);
		const root = mkdtempSync(join(tmpdir(), "workbench-strava-token-"));
		const path = join(root, "nested", "token.json");
		try {
			const tokens = storeTokenResponse(
				{ access_token: "new-access", refresh_token: "rotated-refresh", expires_at: 1234 },
				path,
			);
			expect(tokens).toEqual({
				accessToken: "new-access",
				refreshToken: "rotated-refresh",
				expiresAt: 1_234_000,
			});
			expect(JSON.parse(readFileSync(path, "utf8"))).toEqual(tokens);
			expect(statSync(join(root, "nested")).mode & 0o777).toBe(0o700);
			expect(statSync(path).mode & 0o777).toBe(0o600);
		} finally {
			rmSync(root, { recursive: true, force: true });
		}
	});

	test("accepts only the expected OAuth callback state", () => {
		expect(oauthCallbackCode(new URL("http://localhost/callback?code=ok&state=expected"), "expected")).toBe(
			"ok",
		);
		expect(() =>
			oauthCallbackCode(new URL("http://localhost/callback?code=ok&state=wrong"), "expected"),
		).toThrow("state mismatch");
		expect(() =>
			oauthCallbackCode(new URL("http://localhost/callback?error=denied&state=expected"), "expected"),
		).toThrow("denied");
	});

	test("rejects malformed token responses without writing them", () => {
		expect(() => storeTokenResponse({})).toThrow("access_token or refresh_token");
		expect(() =>
			storeTokenResponse({ access_token: "access", refresh_token: "refresh", expires_at: "nope" }),
		).toThrow("expires_at");
	});

	test("builds activity URLs only against strava.com with bounded paging", () => {
		const url = buildActivitiesUrl({ after: 1700000000, perPage: 20 });
		expect(url.startsWith("https://www.strava.com/api/v3/athlete/activities")).toBe(true);
		expect(url).toContain("per_page=20");
		expect(url).toContain("after=1700000000");
		expect(url).not.toContain("before=");
	});

	test("formats an activity line with derived units", () => {
		const line = formatActivity({
			id: 42,
			name: "Morning Run",
			type: "Run",
			start_date_local: "2026-07-22T07:00:00Z",
			distance: 10250,
			moving_time: 3000,
			total_elevation_gain: 120,
			average_heartrate: 151.4,
		});
		expect(line).toContain("42");
		expect(line).toContain("10.3km");
		expect(line).toContain("50min");
		expect(line).toContain("↑120m");
		expect(line).toContain("151bpm");
	});

	test("tolerates sparse activity payloads", () => {
		expect(formatActivity({})).toContain("(untitled)");
	});

	test("includes swim totals promised by the stats contract", () => {
		const lines = formatAthleteStats({
			recent_swim_totals: { count: 2, distance: 3000, moving_time: 3600 },
			ytd_swim_totals: { count: 12, distance: 24000, moving_time: 28800 },
			all_swim_totals: { count: 80, distance: 180000, moving_time: 180000 },
		});
		expect(lines.join("\n")).toContain("Recent swims");
		expect(lines.join("\n")).toContain("YTD swims");
		expect(lines.join("\n")).toContain("All-time swims");
	});
});
