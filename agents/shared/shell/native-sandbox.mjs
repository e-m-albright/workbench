// The Python entrypoint starts this supervisor with a fresh environment.
// Keep the upstream pinned: the policy adapter rejects an unfamiliar argv shape.
import { spawn } from "node:child_process";
import { rm } from "node:fs/promises";
import { isIP } from "node:net";
import { fileURLToPath } from "node:url";
import path from "node:path";

const plan = JSON.parse(process.argv[2]);
process.env.WORKBENCH_SUPERVISOR_PID = String(process.pid);
const runtime = new URL("../native/node_modules/@anthropic-ai/sandbox-runtime/dist/index.js", import.meta.url);
const { SandboxManager, SandboxRuntimeConfigSchema } = await import(runtime.href);
const { containsGlobChars, normalizePathForSandbox, removeTrailingGlobSuffix, denyGlobRegex, globToRegex } =
  await import(new URL("./sandbox/sandbox-utils.js", runtime).href);
const adapter = fileURLToPath(new URL("native-sandbox.py", import.meta.url));
const quote = (value) => `'${value.replaceAll("'", `'"'"'`)}'`;
let child;
function completion(process) {
  // fd 3 belongs only to the sandbox guardian; vendor exec closes it. The
  // guardian reports vendor exit before killing its entire sandbox, including itself.
  let status = "";
  process.stdio[3].on("data", (data) => { status += data; if (status.length > 8) status = "invalid"; });
  return new Promise((resolve, reject) => {
    process.once("error", reject);
    process.once("close", (code, signal) => {
      const reported = /^\d{1,3}\n$/.test(status) ? Number(status.trim()) : -1;
      resolve(signal === "SIGKILL" && reported >= 0 && reported <= 255
        ? reported : (code || (signal === "SIGINT" ? 130 : 1)));
    });
  });
}
// Owner/project denials are not carve-outs. Use the pinned backend's path
// semantics, but emit these after every allow and pin ancestors against rename.
function mandatoryRules() {
  const rules = [];
  const pins = new Set();
  for (const [paths, operation] of [[plan.mandatory_read || [], "file-read*"], [plan.mandatory_write || [], "file-write*"]]) {
    for (const raw of paths) {
      const normalized = normalizePathForSandbox(removeTrailingGlobSuffix(raw));
      const filter = (value) => containsGlobChars(value)
        ? `(regex ${JSON.stringify(denyGlobRegex(value))})`
        : `(subpath ${JSON.stringify(value)})`;
      rules.push(`(deny ${operation} file-write-unlink ${filter(normalized)})`);
      // A wildcard ancestor must not be renamed to take descendants outside
      // the denied pattern. Literal ancestors are pinned only at their vnode.
      for (let ancestor = path.dirname(normalized); ancestor !== "/"; ancestor = path.dirname(ancestor)) {
        // /** names no ancestor: renaming one preserves a global suffix deny.
        // Pinning it would prohibit every directory removal, including locks.
        if (ancestor === "/**") continue;
        pins.add(containsGlobChars(ancestor)
          ? `(regex ${JSON.stringify(globToRegex(ancestor))})`
          : `(literal ${JSON.stringify(ancestor)})`);
      }
    }
  }
  if (pins.size) rules.push(`(deny file-write-unlink ${[...pins].join(" ")})`);
  return `\n${rules.join("\n")}\n`;
}
const mandatory = mandatoryRules();
async function launch(command, stdio) {
  const wrapped = await SandboxManager.wrapWithSandboxArgv(command.map(quote).join(" "), "/bin/bash");
  if (wrapped.argv.length !== 3 || wrapped.argv[0] !== "/bin/bash" || wrapped.argv[1] !== "-c") {
    throw new Error("Unexpected sandbox runtime launch shape");
  }
  return spawn("/usr/bin/python3", ["-I", "-S", adapter, "--apply", wrapped.argv[2], String(plan.browser_port || 0), mandatory, JSON.stringify(plan.ports ?? [])], {
    cwd: plan.cwd, env: wrapped.env, stdio: [stdio, stdio, stdio, "pipe"],
  });
}
try {
  const policy = SandboxRuntimeConfigSchema.parse(plan.policy);
  // Public TCP tunnels on web ports are intentional, not protocol inspection.
  // WHATWG host parsing canonicalizes numeric shorthand before literal checks.
  await SandboxManager.initialize(policy, async ({ host, port }) => {
    let canonical;
    try { canonical = new URL(`http://${host}`).hostname.replace(/^\[|\]$/g, "").replace(/\.$/, ""); }
    catch { return false; }
    return !isIP(canonical) && canonical !== "localhost" &&
      !canonical.endsWith(".localhost") && !canonical.endsWith(".local") &&
      (port === 80 || port === 443);
  });
  child = await launch(plan.command, "inherit");
  process.on("SIGTERM", () => child.kill("SIGTERM"));
  // Roles assumed from SSO last an hour; keep the session's keys current from the host.
  // A failed refresh swaps the keys for an error naming the sign-in; the next success restores them.
  if (plan.aws_refresh) {
    const refresh = JSON.stringify(plan.aws_refresh);
    const timer = setInterval(() => {
      spawn("/usr/bin/python3", ["-I", "-S", adapter, "--refresh-aws", refresh], {
        env: { PATH: "/usr/bin:/bin" }, stdio: "ignore",
      }).on("error", () => {});
    }, 5 * 60 * 1000);
    child.once("exit", () => clearInterval(timer));
  }
  // Terminal SIGINT already reaches the child; keep the proxy alive during its cleanup.
  process.on("SIGINT", () => {});
  process.exitCode = await completion(child);
  if (plan.resume_hint && process.stderr.isTTY) console.error(plan.resume_hint);
} catch (error) {
  console.error(`native sandbox: ${error.message}`);
  process.exitCode = 1;
} finally {
  if (child && plan.browser_port) {
    // Cleanup runs inside the same boundary: never trust agent-writable PID files
    // to signal a host process. --all is confined to this session's socket directory.
    try {
      const cleanup = await launch(["agent-browser", "close", "--all"], "ignore");
      const timeout = setTimeout(() => cleanup.kill("SIGKILL"), 5000);
      const code = await completion(cleanup);
      clearTimeout(timeout);
      if (code !== 0) throw new Error("browser cleanup did not complete");
    } catch (error) {
      console.error(`native sandbox: ${error.message}`);
      process.exitCode = 1;
    }
  }
  await SandboxManager.reset();
  if (/^\/private\/tmp\/wb-native-[a-zA-Z0-9_-]+$/.test(plan.env.TMPDIR)) {
    await rm(plan.env.TMPDIR, { recursive: true, force: true });
  }
}
