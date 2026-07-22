import { existsSync, readFileSync } from "node:fs";
import { join, normalize, resolve } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { getAgentDir } from "@earendil-works/pi-coding-agent";

interface DenyCommandRule {
  name: string;
  patterns: string[];
}

export interface PermissionPolicy {
  defaultAction?: "allow" | "deny";
  denyCommands?: DenyCommandRule[];
  protectedPaths?: string[];
  protectedReadPaths?: string[];
  protectedWritePaths?: string[];
}

export type LoadedPermissionPolicy = {
  defaultAction: "allow" | "deny";
  denyCommands: DenyCommandRule[];
  protectedReadPaths: string[];
  protectedWritePaths: string[];
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
  "~/.claude/.credentials.json",
  "~/.codex/auth.json",
  "~/Library/Keychains/**",
];

const FALLBACK_POLICY: LoadedPermissionPolicy = {
  defaultAction: "allow",
  denyCommands: [],
  protectedReadPaths: SECRET_PATHS,
  protectedWritePaths: [...SECRET_PATHS, ".git/**", "node_modules/**"],
};

function readPolicyFile(path: string): PermissionPolicy {
  if (!existsSync(path)) return {};
  try {
    return JSON.parse(readFileSync(path, "utf8")) as PermissionPolicy;
  } catch (error) {
    throw new Error(`Invalid permission policy at ${path}: ${error}`);
  }
}

function loadPolicy(cwd: string): LoadedPermissionPolicy {
  const globalPolicy = readPolicyFile(join(getAgentDir(), "permission-policy.json"));
  const projectPolicy = readPolicyFile(join(cwd, ".pi", "permission-policy.json"));
  const legacyPaths = [...(globalPolicy.protectedPaths ?? []), ...(projectPolicy.protectedPaths ?? [])];

  return {
    defaultAction: projectPolicy.defaultAction ?? globalPolicy.defaultAction ?? FALLBACK_POLICY.defaultAction,
    denyCommands: [
      ...FALLBACK_POLICY.denyCommands,
      ...(globalPolicy.denyCommands ?? []),
      ...(projectPolicy.denyCommands ?? []),
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
  const withoutQuotes = candidate.replace(/^['\"]|['\"]$/g, "");
  if (withoutQuotes.startsWith("~")) return normalize(withoutQuotes.replace(/^~/, process.env.HOME ?? "~"));
  if (withoutQuotes.startsWith("/")) return normalize(withoutQuotes);
  return normalize(resolve(cwd, withoutQuotes));
}

export function pathMatchesPolicy(cwd: string, path: string, protectedPathGlobs: string[]): string | undefined {
  const normalized = normalizeCandidatePath(cwd, path);
  const relative = normalize(path.replace(/^\.\//, ""));

  for (const glob of protectedPathGlobs) {
    const regex = globToRegExp(glob);
    if (regex.test(normalized) || regex.test(relative)) return glob;
  }

  return undefined;
}

function extractInputPaths(input: unknown): string[] {
  if (!input || typeof input !== "object") return [];
  const record = input as Record<string, unknown>;
  const paths = new Set<string>();

  for (const key of ["path", "file", "target", "source"] as const) {
    const value = record[key];
    if (typeof value === "string") paths.add(value);
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

function protectedPathMention(cwd: string, command: string, protectedPathGlobs: string[]): string | undefined {
  const tokens = command.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g) ?? [];
  for (const token of tokens) {
    const cleaned = token.replace(/^['\"]|['\"]$/g, "");
    const looksLikePath = cleaned.includes("/") || cleaned.startsWith(".") || cleaned.startsWith("~");
    if (!looksLikePath) continue;

    const matched = pathMatchesPolicy(cwd, cleaned, protectedPathGlobs);
    if (matched) return matched;
  }
  return undefined;
}

export function commandDenyReason(command: string, rules: DenyCommandRule[]): string | undefined {
  for (const rule of rules) {
    for (const pattern of rule.patterns) {
      if (new RegExp(pattern, "i").test(command)) return rule.name;
    }
  }
  return undefined;
}

function block(reason: string) {
  return { block: true, reason };
}

export function policyBlockReason(
  toolName: string,
  input: unknown,
  cwd: string,
  policy: LoadedPermissionPolicy,
): string | undefined {
  const readTools = new Set(["read", "grep", "find", "ls"]);
  const writeTools = new Set(["write", "edit"]);
  const protectedPaths = readTools.has(toolName)
    ? policy.protectedReadPaths
    : writeTools.has(toolName)
      ? policy.protectedWritePaths
      : [];
  for (const candidate of extractInputPaths(input)) {
    const matched = pathMatchesPolicy(cwd, candidate, protectedPaths);
    if (matched) return `Protected path blocked by policy: ${matched}`;
  }

  if (toolName !== "bash") return undefined;
  const command = String((input as Record<string, unknown>).command ?? "");
  const protectedPath = protectedPathMention(cwd, command, policy.protectedReadPaths);
  if (protectedPath) return `Command mentions protected path: ${protectedPath}`;
  const denied = commandDenyReason(command, policy.denyCommands);
  if (denied) return `Command blocked by policy: ${denied}`;
  if (policy.defaultAction === "deny") return "Command blocked by default-deny policy";
  return undefined;
}

export default function permissionPolicyExtension(pi: ExtensionAPI) {
  let lastPolicy: LoadedPermissionPolicy | undefined;

  function policyFor(ctx: ExtensionContext) {
    lastPolicy = loadPolicy(ctx.cwd);
    return lastPolicy;
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
          `  Protected read globs: ${policy.protectedReadPaths.length}`,
          `  Protected write globs: ${policy.protectedWritePaths.length}`,
          "  Source: ~/.pi/agent/permission-policy.json plus optional .pi/permission-policy.json",
        ].join("\n"),
        "info",
      );
    },
  });

  pi.on("tool_call", async (event, ctx) => {
    const reason = policyBlockReason(event.toolName, event.input, ctx.cwd, policyFor(ctx));
    return reason ? block(reason) : undefined;
  });
}
