import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { type ExtensionAPI, getExamplesPath } from "@earendil-works/pi-coding-agent";

// Follow the installed Pi version rather than maintaining a fork of its example.
export default async function subagent(pi: ExtensionAPI) {
	const source = pathToFileURL(join(getExamplesPath(), "extensions/subagent/index.ts")).href;
	const upstream = await import(source);
	upstream.default(pi);
}
