import { homedir } from "node:os";
import { join } from "node:path";

export function resolveAgentDir(
	env: Readonly<Record<string, string | undefined>> = process.env,
	home: string = homedir(),
): string {
	return env.PI_CODING_AGENT_DIR || join(home, ".pi", "agent");
}
