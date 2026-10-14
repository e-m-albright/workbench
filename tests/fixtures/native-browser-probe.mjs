// Synthetic acceptance for the installed CLI and Pi's installed process wrapper.
import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { promisify } from "node:util";
import { pathToFileURL } from "node:url";

const exec = promisify(execFile);
const output = process.argv[2];
const kind = process.argv[3] || "cli";
await writeFile(`${output}/runtime.json`, JSON.stringify({
  args: process.env.AGENT_BROWSER_ARGS,
  scratch: process.env.TMPDIR,
}));
let wrapper;
if (kind === "pi") {
  ({ runAgentBrowserProcess: wrapper } = await import(pathToFileURL(
    `${process.env.WORKBENCH_HOST_HOME}/.pi/agent/npm/node_modules/pi-agent-browser-native/dist/extensions/agent-browser/lib/process.js`,
  )));
}
const run = async (...args) => {
  const argv = ["--session", "acceptance", ...args];
  if (!wrapper) return (await exec("agent-browser", argv, { timeout: 30000 })).stdout;
  const result = await wrapper({ args: argv, cwd: process.cwd(), timeoutMs: 30000 });
  assert.equal(result.exitCode, 0, JSON.stringify({ ...result, spawnError: String(result.spawnError) }));
  return result.stdout;
};
try {
  await run("open", "https://example.com");
  assert.match(await run("snapshot"), /documentation examples/);
  const html = "<!doctype html><title>Browser acceptance</title><h1>Protected browser acceptance</h1><p>Synthetic content only.</p><button onclick=\"this.textContent='Interaction passed'\">Check</button>";
  await writeFile(`${output}/fixture.html`, html);
  await run("open", pathToFileURL(`${output}/fixture.html`).href);
  await run("click", "button");
  assert.match(await run("snapshot"), /Interaction passed/);
  await run("screenshot", `${output}/${kind}.png`);
  await run("pdf", `${output}/${kind}.pdf`);
  assert.match((await exec("pdftotext", [`${output}/${kind}.pdf`, "-"])).stdout, /Protected browser acceptance/);
  await exec("pdftoppm", ["-f", "1", "-singlefile", "-scale-to", "1000", "-png", `${output}/${kind}.pdf`, `${output}/${kind}-pdf`]);
  // A real browser must remain unable to read protected files, not merely its CLI.
  await run("open", pathToFileURL(`${output}/.env`).href).catch(() => {});
  assert.doesNotMatch(await run("snapshot"), /SYNTHETIC_PRIVATE_SENTINEL/);
  await assert.rejects(readFile(`${output}/.env`));
  console.log(`${kind}: public navigation, synthetic interaction, screenshot, PDF, and private-file denial PASS`);
} finally {
  // Optional omission exercises the launch supervisor's cleanup on agent exit.
  if (!process.argv.includes("--leave-open")) await run("close");
}
