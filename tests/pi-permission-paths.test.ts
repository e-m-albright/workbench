import { afterEach, expect, test, vi } from "vitest";

const realpath = vi.fn(() => {
	throw Object.assign(new Error("Permission denied"), { code: "EPERM" });
});
vi.doMock("node:fs", async () => ({
	...(await vi.importActual<typeof import("node:fs")>("node:fs")),
	realpathSync: realpath,
}));
vi.doMock("@earendil-works/pi-coding-agent", () => ({}));
const { pathMatchesPolicy } = await import("../agents/pi/extensions/permission-policy");
afterEach(() => realpath.mockClear());

test("known protected paths are denied without resolving inaccessible storage", () => {
	expect(
		pathMatchesPolicy("/example", "/example/group.com.apple.notes/NoteStore.sqlite", [
			"**/secrets/**",
			"**/group.com.apple.notes/**",
		]),
	).toBe("**/group.com.apple.notes/**");
	expect(realpath).not.toHaveBeenCalled();
});

test("an empty rule list does not resolve the candidate path", () => {
	expect(pathMatchesPolicy("/example", "/example/inaccessible", [])).toBeUndefined();
	expect(realpath).not.toHaveBeenCalled();
});

test("an unresolved possible alias still fails closed", () => {
	expect(() => pathMatchesPolicy("/example", "alias/file", ["**/secrets/**"])).toThrow("Permission denied");
});
