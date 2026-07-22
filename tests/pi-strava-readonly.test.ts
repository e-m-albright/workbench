import { describe, expect, mock, test } from "bun:test";

mock.module("@earendil-works/pi-coding-agent", () => ({ getAgentDir: () => "/tmp/pi-agent" }));
// typebox is a virtual module provided by Pi's extension loader at runtime.
mock.module("typebox", () => {
	const schema = () => ({});
	return { Type: { Object: schema, String: schema, Number: schema, Optional: schema } };
});
const { buildActivitiesUrl, formatActivity } = await import("../agents/pi/extensions/strava-readonly");

describe("Pi Strava read-only connector", () => {
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
});
