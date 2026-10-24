// GHSA-mrhx-c7xc-m3w5 must be fixed without changing the sandbox's v3 API.
const assert = require("node:assert/strict");
const { createRequire } = require("node:module");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const fromRuntime = createRequire(path.resolve(process.argv[2], "package.json"));
const { z: v4 } = fromRuntime("zod/v4");
const oversized = v4.array(v4.string()).max(1).safeParse(Array(50).fill(123));
assert.equal(oversized.success, false);
assert.equal(oversized.error.issues.length, 1, "Oversized arrays must stop before per-item errors");
assert.equal(oversized.error.issues[0].code, "too_big");

async function verifyCompatibility() {
  const { SandboxRuntimeConfigSchema } = await import(
    pathToFileURL(fromRuntime.resolve("@anthropic-ai/sandbox-runtime")).href
  );
  assert.equal(SandboxRuntimeConfigSchema._def.typeName, "ZodEffects");
  const config = {
    network: { allowedDomains: ["example.com"], deniedDomains: [] },
    filesystem: { denyRead: [], allowWrite: ["/tmp"], denyWrite: [] },
  };
  const parsed = SandboxRuntimeConfigSchema.parse(config);
  assert.deepEqual(parsed.network.allowedDomains, config.network.allowedDomains);
  assert.deepEqual(parsed.filesystem.allowWrite, config.filesystem.allowWrite);
  assert.equal(SandboxRuntimeConfigSchema.safeParse({ ...config, network: { allowedDomains: [123] } }).success, false);
  assert.equal(SandboxRuntimeConfigSchema.safeParse({ ...config, filesystem: { allowWrite: [{ path: "/tmp" }] } }).success, false);
  console.log("Verified patched Zod v4 array limits and sandbox v3 schema compatibility");
}
verifyCompatibility().catch((error) => { console.error(error); process.exitCode = 1; });
