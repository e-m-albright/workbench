// The Python entrypoint starts this supervisor with a fresh environment.
// Keep the upstream pinned: the policy adapter rejects an unfamiliar argv shape.
import { spawn } from "node:child_process";
import { rm } from "node:fs/promises";
import { isIP } from "node:net";
import { fileURLToPath } from "node:url";

const plan = JSON.parse(process.argv[2]);
const runtime = new URL("../native/node_modules/@anthropic-ai/sandbox-runtime/dist/index.js", import.meta.url);
const { SandboxManager, SandboxRuntimeConfigSchema } = await import(runtime.href);
const adapter = fileURLToPath(new URL("native-sandbox.py", import.meta.url));
const quote = (value) => `'${value.replaceAll("'", `'"'"'`)}'`;
let child;
try {
  const policy = SandboxRuntimeConfigSchema.parse(plan.policy);
  // Public HTTP(S) is intentional. The upstream proxy checks resolved addresses
  // before dialing; literal addresses and non-web destination ports stay denied.
  await SandboxManager.initialize(policy, async ({ host, port }) =>
    !isIP(host) && !host.endsWith(".localhost") && !host.endsWith(".local") &&
    (port === 80 || port === 443));
  const command = plan.command.map(quote).join(" ");
  const wrapped = await SandboxManager.wrapWithSandboxArgv(command, "/bin/bash");
  if (wrapped.argv.length !== 3 || wrapped.argv[0] !== "/bin/bash" || wrapped.argv[1] !== "-c") {
    throw new Error("Unexpected sandbox runtime launch shape");
  }
  child = spawn("/usr/bin/python3", ["-I", "-S", adapter, "--apply", wrapped.argv[2]], {
    cwd: plan.cwd, env: wrapped.env, stdio: "inherit",
  });
  process.on("SIGTERM", () => child.kill("SIGTERM"));
  // Terminal SIGINT already reaches the child; keep the proxy alive during its cleanup.
  process.on("SIGINT", () => {});
  process.exitCode = await new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("exit", (code, signal) => resolve(code ?? (signal === "SIGINT" ? 130 : 1)));
  });
} catch (error) {
  console.error(`native sandbox: ${error.message}`);
  process.exitCode = 1;
} finally {
  await SandboxManager.reset();
  if (/^\/private\/tmp\/wb-native-[a-zA-Z0-9_-]+$/.test(plan.env.TMPDIR)) {
    await rm(plan.env.TMPDIR, { recursive: true, force: true });
  }
}
