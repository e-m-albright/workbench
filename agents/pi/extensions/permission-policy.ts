import { chmodSync, existsSync, readFileSync, realpathSync } from "node:fs";
import { join, normalize, resolve } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { resolveAgentDir } from "./lib/agent-dir";

interface DenyCommandRule {
	name: string;
	patterns: string[];
	privateOnly?: boolean;
}

export interface PermissionPolicy {
	defaultAction?: "allow" | "deny";
	denyCommands?: DenyCommandRule[];
	blockedTools?: string[];
	privateProviders?: string[];
	privateOnlyTools?: string[];
	privateBrowserDomains?: string[];
	mcpAllowedTools?: string[];
	protectedPaths?: string[];
	protectedReadPaths?: string[];
	protectedWritePaths?: string[];
	privateReadPaths?: string[];
	privateWritePaths?: string[];
	controlWritePaths?: string[];
}

export type LoadedPermissionPolicy = {
	defaultAction: "allow" | "deny";
	denyCommands: DenyCommandRule[];
	blockedTools: string[];
	privateProviders: string[];
	privateOnlyTools: string[];
	privateBrowserDomains: string[];
	mcpAllowedTools: string[];
	protectedReadPaths: string[];
	protectedWritePaths: string[];
	privateReadPaths: string[];
	privateWritePaths: string[];
	controlWritePaths: string[];
};

const SECRET_PATHS = [
	".env",
	".env.*",
	"**/.env",
	"**/.env.*",
	"**/secrets/**",
	"~/.ssh/**",
	"~/.gnupg/**",
	"~/.aws/**",
	"~/.config/gh/hosts.yml",
	"~/.pi/agent/auth.json",
	"~/Library/Application Support/notes-app/**",
	"~/.claude.json",
	"~/Library/Application Support/Claude/claude_desktop_config.json",
	"~/.claude/.credentials.json",
	"~/.codex/auth.json",
	"~/Library/Keychains/**",
];

const FALLBACK_POLICY: LoadedPermissionPolicy = {
	defaultAction: "allow",
	denyCommands: [],
	blockedTools: [],
	privateProviders: ["omlx"],
	privateOnlyTools: [],
	privateBrowserDomains: [],
	mcpAllowedTools: [],
	protectedReadPaths: SECRET_PATHS,
	protectedWritePaths: [...SECRET_PATHS, "~/.pi/agent/**", ".git/**", "node_modules/**"],
	privateReadPaths: [],
	privateWritePaths: [],
	controlWritePaths: [],
};

function readPolicyFile(path: string): PermissionPolicy {
	if (!existsSync(path)) return {};
	try {
		return JSON.parse(readFileSync(path, "utf8")) as PermissionPolicy;
	} catch (error) {
		throw new Error(`Invalid permission policy at ${path}: ${error}`);
	}
}

export function readPrivatePathFile(
	path = join(process.env.HOME ?? "~", ".config", "workbench", "private-paths"),
): string[] {
	if (!existsSync(path)) return [];
	return readFileSync(path, "utf8")
		.split(/\r?\n/)
		.map((line) => line.trim())
		.filter((line) => line.length > 0 && !line.startsWith("#"));
}

function loadPolicy(cwd: string): LoadedPermissionPolicy {
	const globalPolicy = readPolicyFile(join(resolveAgentDir(), "permission-policy.json"));
	const projectPolicy = readPolicyFile(join(cwd, ".pi", "permission-policy.json"));
	const legacyPaths = [...(globalPolicy.protectedPaths ?? []), ...(projectPolicy.protectedPaths ?? [])];

	return {
		defaultAction: projectPolicy.defaultAction ?? globalPolicy.defaultAction ?? FALLBACK_POLICY.defaultAction,
		denyCommands: [
			...FALLBACK_POLICY.denyCommands,
			...(globalPolicy.denyCommands ?? []),
			...(projectPolicy.denyCommands ?? []),
		],
		blockedTools: [
			...FALLBACK_POLICY.blockedTools,
			...(globalPolicy.blockedTools ?? []),
			...(projectPolicy.blockedTools ?? []),
		],
		privateProviders: (globalPolicy.privateProviders ?? FALLBACK_POLICY.privateProviders).filter(
			(provider) => provider === "omlx",
		),
		privateOnlyTools: [
			...FALLBACK_POLICY.privateOnlyTools,
			...(globalPolicy.privateOnlyTools ?? []),
			...(projectPolicy.privateOnlyTools ?? []),
		],
		privateBrowserDomains: [
			...FALLBACK_POLICY.privateBrowserDomains,
			...(globalPolicy.privateBrowserDomains ?? []),
			...(projectPolicy.privateBrowserDomains ?? []),
		],
		mcpAllowedTools: [
			...FALLBACK_POLICY.mcpAllowedTools,
			...(globalPolicy.mcpAllowedTools ?? []),
			...(projectPolicy.mcpAllowedTools ?? []),
		],
		protectedReadPaths: [
			...(globalPolicy.protectedReadPaths ?? FALLBACK_POLICY.protectedReadPaths),
			...(projectPolicy.protectedReadPaths ?? []),
			...legacyPaths,
		],
		protectedWritePaths: [
			...(globalPolicy.protectedWritePaths ?? FALLBACK_POLICY.protectedWritePaths),
			...(projectPolicy.protectedWritePaths ?? []),
			...legacyPaths,
		],
		privateReadPaths: [
			...FALLBACK_POLICY.privateReadPaths,
			...(globalPolicy.privateReadPaths ?? []),
			...(projectPolicy.privateReadPaths ?? []),
			...readPrivatePathFile(),
		],
		privateWritePaths: [
			...FALLBACK_POLICY.privateWritePaths,
			...(globalPolicy.privateWritePaths ?? []),
			...(projectPolicy.privateWritePaths ?? []),
			...readPrivatePathFile(),
		],
		controlWritePaths: [
			...FALLBACK_POLICY.controlWritePaths,
			...(globalPolicy.controlWritePaths ?? []),
			...(projectPolicy.controlWritePaths ?? []),
		],
	};
}

function globToRegExp(glob: string): RegExp {
	let pattern = glob.replace(/^~(?=\/|$)/, process.env.HOME ?? "~");
	pattern = normalize(pattern);

	const escaped = pattern
		.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
		.replace(/\\\*\\\*/g, ".*")
		.replace(/\\\*/g, "[^/]*");

	return new RegExp(`(^|/)${escaped}($|/)`, "i");
}

function normalizeCandidatePath(cwd: string, candidate: string): string {
	// Strip wrapping quotes plus trailing shell punctuation a command substitution
	// leaves attached, e.g. `$(cat ~/.pi/agent/auth.json)` tokenizes with `)`.
	const withoutQuotes = candidate
		.replace(/^[('"`]+|[)'"`;,]+$/g, "")
		.replace(/^\$\{HOME\}|^\$HOME/, process.env.HOME ?? "~");
	if (withoutQuotes.startsWith("~")) return normalize(withoutQuotes.replace(/^~/, process.env.HOME ?? "~"));
	if (withoutQuotes.startsWith("/")) return normalize(withoutQuotes);
	return normalize(resolve(cwd, withoutQuotes));
}

export function pathMatchesPolicy(
	cwd: string,
	path: string,
	protectedPathGlobs: string[],
): string | undefined {
	const normalized = normalizeCandidatePath(cwd, path);
	const relative = normalize(path.replace(/^\.\//, ""));
	// A symlink inside the project can point at a protected file; match the
	// resolved target too, not just the literal string.
	let resolvedReal: string | undefined;
	try {
		if (existsSync(normalized)) {
			const real = realpathSync(normalized);
			if (real !== normalized) resolvedReal = real;
		}
	} catch {
		resolvedReal = undefined;
	}

	for (const glob of protectedPathGlobs) {
		const regex = globToRegExp(glob);
		if (regex.test(normalized) || regex.test(relative)) return glob;
		if (resolvedReal && regex.test(resolvedReal)) return glob;
	}

	return undefined;
}

function extractInputPaths(input: unknown): string[] {
	if (!input || typeof input !== "object") return [];
	const record = input as Record<string, unknown>;
	const paths = new Set<string>();

	for (const key of ["path", "file", "target", "source", "outputPath"] as const) {
		const value = record[key];
		if (typeof value === "string") paths.add(value);
	}

	const args = record.args;
	if (Array.isArray(args)) {
		for (const value of args) {
			if (typeof value === "string") paths.add(value);
		}
	}

	const job = record.job;
	if (job && typeof job === "object") {
		const steps = (job as Record<string, unknown>).steps;
		if (Array.isArray(steps)) {
			for (const step of steps) {
				if (!step || typeof step !== "object") continue;
				const stepPath = (step as Record<string, unknown>).path;
				if (typeof stepPath === "string") paths.add(stepPath);
			}
		}
	}

	const multi = record.multi;
	if (Array.isArray(multi)) {
		for (const item of multi) {
			if (!item || typeof item !== "object") continue;
			const itemPath = (item as Record<string, unknown>).path;
			if (typeof itemPath === "string") paths.add(itemPath);
		}
	}

	return [...paths];
}

function allInputStrings(value: unknown): string[] {
	if (typeof value === "string") return [value];
	if (Array.isArray(value)) return value.flatMap(allInputStrings);
	if (!value || typeof value !== "object") return [];
	return Object.values(value as Record<string, unknown>).flatMap(allInputStrings);
}

function privateBrowserDomain(input: unknown, domains: string[]): string | undefined {
	for (const value of allInputStrings(input)) {
		const lowered = value.toLowerCase();
		for (const domain of domains) {
			const needle = domain.toLowerCase();
			if (lowered.includes(`://${needle}`) || lowered.includes(`://${needle}/`)) return domain;
			if (lowered.includes(`.${needle}/`) || lowered.endsWith(`.${needle}`)) return domain;
		}
	}
	return undefined;
}

function protectedPathMention(
	cwd: string,
	command: string,
	protectedPathGlobs: string[],
): string | undefined {
	// Two passes: quoted-token matching preserves paths with spaces, and a
	// metacharacter split exposes paths embedded in substitutions like $(cat X).
	const tokens = [
		...(command.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g) ?? []),
		...command.split(/[\s$`()|;&<>"']+/),
	];
	for (const token of tokens) {
		const cleaned = token.replace(/^[('"`]+|[)'"`;,]+$/g, "");
		const looksLikePath =
			cleaned.includes("/") ||
			cleaned.startsWith(".") ||
			cleaned.startsWith("~") ||
			cleaned.startsWith("$HOME") ||
			existsSync(resolve(cwd, cleaned));
		if (!looksLikePath) continue;

		const matched = pathMatchesPolicy(cwd, cleaned, protectedPathGlobs);
		if (matched) return matched;
	}
	return undefined;
}

export function commandDenyReason(
	command: string,
	rules: DenyCommandRule[],
	privateProvider = false,
	openData = false,
): string | undefined {
	for (const rule of rules) {
		if (rule.privateOnly && (privateProvider || (openData && rule.name === "Notes private data access")))
			continue;
		for (const pattern of rule.patterns) {
			if (new RegExp(pattern, "i").test(command)) return rule.name;
		}
	}
	return undefined;
}

const DENY_ALTERNATIVES: Record<string, string> = {
	"Gmail access": "Switch to the private local provider before accessing Gmail.",
	"Notes private data access": "Switch to the private local provider before querying private Notes data.",
	"nested agent invocation":
		"Nested agent processes are disabled so a cloud model cannot use a local model as a data proxy.",
	"filesystem mutation command":
		"Use workspace_files for rename, copy, or directory creation; use write or edit for file contents.",
	"shell network retrieval, upload, or remote script execution":
		"Use agent_browser or agent_browser_web_search for external reads and a dedicated confirmed tool for mutations.",
	"shell file redirection": "Use write or edit instead of shell redirection.",
	"inline interpreter escape hatch":
		"Use read/edit/write for bounded changes, or add a reviewed script file and execute that file directly.",
	"destructive or history-changing git":
		"Use the safe Git workflow and obtain the required user confirmation instead of retrying the shell command.",
	"mutating GitHub CLI command":
		"Use github_workflow_dispatch for confirmed workflow runs; other GitHub mutations require an explicit supported tool.",
	"dependency installation or removal":
		"Use the repository's existing setup recipe or ask the user to approve the exact dependency change.",
};

export function formatCommandDenial(reason: string): string {
	const alternative = DENY_ALTERNATIVES[reason];
	return alternative
		? `Command blocked by policy: ${reason}. ${alternative}`
		: `Command blocked by policy: ${reason}`;
}

function block(reason: string) {
	return { block: true, reason };
}

function hardenSessionFile(sessionFile: string | undefined): void {
	if (!sessionFile) return;
	try {
		chmodSync(sessionFile, 0o600);
	} catch (error) {
		// Pi can expose the target path before creating it while rebinding a session.
		// Retry at the first model turn, when the transcript has been persisted.
		if ((error as { code?: string }).code === "ENOENT") return;
		throw error;
	}
}

export function policyBlockReason(
	toolName: string,
	input: unknown,
	cwd: string,
	policy: LoadedPermissionPolicy,
	provider?: string,
	mode = process.env.WORKBENCH_PI_MODE,
): string | undefined {
	const privateProvider =
		mode === "local-unrestricted" && provider === "omlx" && policy.privateProviders.includes(provider);
	const dataAuthorized = privateProvider || mode === "hosted-unrestricted";
	const control = mode?.endsWith("-unrestricted") ?? false;
	if (policy.blockedTools.includes(toolName)) {
		return `Tool blocked by policy: ${toolName}`;
	}
	if (policy.privateOnlyTools.includes(toolName) && !privateProvider) {
		return `Tool requires a private local provider: ${toolName}`;
	}
	if (toolName === "agent_browser" && !privateProvider) {
		const domain = privateBrowserDomain(input, policy.privateBrowserDomains);
		if (domain) return `Authenticated private browser domain requires a private local provider: ${domain}`;
	}

	const readTools = new Set(["read", "grep", "find", "ls", "agent_browser"]);
	const writeTools = new Set(["write", "edit", "workspace_files"]);
	const protectedPaths = readTools.has(toolName)
		? policy.protectedReadPaths
		: writeTools.has(toolName)
			? policy.protectedWritePaths
			: [];
	const controlPaths = writeTools.has(toolName) && !control ? policy.controlWritePaths : [];
	const privatePaths = readTools.has(toolName)
		? policy.privateReadPaths
		: writeTools.has(toolName)
			? policy.privateWritePaths
			: [];
	for (const candidate of extractInputPaths(input)) {
		const matched = pathMatchesPolicy(cwd, candidate, protectedPaths);
		if (matched) return `Protected path blocked by policy: ${matched}`;
		const controlled = pathMatchesPolicy(cwd, candidate, controlPaths);
		if (controlled) return `hosted-unrestricted authority required to write control path: ${controlled}`;
		const privateMatched = pathMatchesPolicy(cwd, candidate, privatePaths);
		if (privateMatched && toolName === "agent_browser") {
			return `Private path browser upload blocked by policy: ${privateMatched}`;
		}
		if (privateMatched && !dataAuthorized) {
			return `Private path requires a private local provider: ${privateMatched}`;
		}
	}

	if (toolName === "mcp") {
		const params = (input ?? {}) as Record<string, unknown>;
		const action = typeof params.action === "string" ? params.action : undefined;
		if (action === "auth-start" || action === "auth-complete") {
			return "MCP OAuth must be initiated explicitly with /mcp-auth";
		}
		const remoteTool = typeof params.tool === "string" ? params.tool : undefined;
		if (remoteTool && !policy.mcpAllowedTools.includes(remoteTool)) {
			return `MCP tool is not on the read-only allowlist: ${remoteTool}`;
		}
		return undefined;
	}

	if (toolName !== "bash") return undefined;
	const command = String((input as Record<string, unknown>).command ?? "");
	const protectedPath = protectedPathMention(cwd, command, policy.protectedReadPaths);
	if (protectedPath) return `Command mentions protected path: ${protectedPath}`;
	const privatePath = protectedPathMention(cwd, command, policy.privateReadPaths);
	if (privatePath && !dataAuthorized) {
		return `Command mentions private path requiring a private local provider: ${privatePath}`;
	}
	const denied = commandDenyReason(
		command,
		policy.denyCommands,
		privateProvider,
		mode === "hosted-unrestricted",
	);
	if (denied) return formatCommandDenial(denied);
	if (policy.defaultAction === "deny") return "Command blocked by default-deny policy";
	return undefined;
}

export default function permissionPolicyExtension(pi: ExtensionAPI) {
	function policyFor(ctx: ExtensionContext) {
		return loadPolicy(ctx.cwd);
	}

	pi.registerCommand("permissions-status", {
		description: "Show active Pi permission policy summary",
		handler: async (_args, ctx) => {
			const policy = policyFor(ctx);
			ctx.ui.notify(
				[
					"Permission policy",
					`  Default action: ${policy.defaultAction}`,
					`  Deny command groups: ${policy.denyCommands.length}`,
					`  Blocked tools: ${policy.blockedTools.length}`,
					`  Private-only tools: ${policy.privateOnlyTools.length}`,
					`  Private browser domains: ${policy.privateBrowserDomains.length}`,
					`  Private providers: ${policy.privateProviders.join(", ")}`,
					`  MCP read-only tools: ${policy.mcpAllowedTools.length}`,
					`  Protected read globs: ${policy.protectedReadPaths.length}`,
					`  Protected write globs: ${policy.protectedWritePaths.length}`,
					`  Private read globs: ${policy.privateReadPaths.length}`,
					`  Private write globs: ${policy.privateWritePaths.length}`,
					`  Control-only write globs: ${policy.controlWritePaths.length}`,
					"  Source: ~/.pi/agent/permission-policy.json, ~/.config/workbench/private-paths, plus optional .pi/permission-policy.json",
				].join("\n"),
				"info",
			);
		},
	});

	pi.on("session_start", async (_event, ctx) => {
		hardenSessionFile(ctx.sessionManager.getSessionFile());
	});

	pi.on("before_agent_start", async (_event, ctx) => {
		hardenSessionFile(ctx.sessionManager.getSessionFile());
	});

	pi.on("message_end", async (_event, ctx) => {
		hardenSessionFile(ctx.sessionManager.getSessionFile());
	});

	pi.on("tool_call", async (event, ctx) => {
		const reason = policyBlockReason(
			event.toolName,
			event.input,
			ctx.cwd,
			policyFor(ctx),
			ctx.model?.provider,
		);
		return reason ? block(reason) : undefined;
	});
}
