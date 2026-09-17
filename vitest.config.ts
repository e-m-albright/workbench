import { defineConfig } from "vitest/config";

// Pi supplies these APIs at runtime; each test defines only the APIs it uses.
const piApis = new Set([
	"@earendil-works/pi-ai",
	"@earendil-works/pi-coding-agent",
	"@earendil-works/pi-tui",
	"typebox",
]);

export default defineConfig({
	plugins: [{ name: "pi-runtime-apis", resolveId: (id) => (piApis.has(id) ? id : undefined) }],
	test: { include: ["tests/pi-*.test.ts"], isolate: true },
});
