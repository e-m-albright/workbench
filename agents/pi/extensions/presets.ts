import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { getAgentDir } from "@earendil-works/pi-coding-agent";

type ThinkingLevel = "off" | "minimal" | "low" | "medium" | "high" | "xhigh";

interface Preset {
  provider?: string;
  model?: string;
  thinkingLevel?: ThinkingLevel;
  tools?: string[];
  instructions?: string;
}

interface PresetsConfig {
  [name: string]: Preset;
}

interface PresetSettings {
  defaultPreset?: string;
}

function readPresets(path: string): PresetsConfig {
  if (!existsSync(path)) return {};
  return JSON.parse(readFileSync(path, "utf8")) as PresetsConfig;
}

function loadPresets(cwd: string): PresetsConfig {
  return {
    ...readPresets(join(getAgentDir(), "presets.json")),
    ...readPresets(join(cwd, ".pi", "presets.json")),
  };
}

function presetSummary(name: string, preset: Preset): string {
  const parts = [name];
  if (preset.tools) parts.push(`tools:${preset.tools.join(",")}`);
  if (preset.thinkingLevel) parts.push(`thinking:${preset.thinkingLevel}`);
  if (preset.provider && preset.model) parts.push(`${preset.provider}/${preset.model}`);
  return parts.join(" | ");
}

async function applyPreset(name: string, preset: Preset, pi: ExtensionAPI, ctx: ExtensionContext) {
  if (preset.provider && preset.model) {
    const model = ctx.modelRegistry.find(preset.provider, preset.model);
    if (!model) {
      ctx.ui.notify(`Preset ${name}: model not found: ${preset.provider}/${preset.model}`, "warning");
    } else {
      const ok = await pi.setModel(model);
      if (!ok) ctx.ui.notify(`Preset ${name}: model unavailable: ${preset.provider}/${preset.model}`, "warning");
    }
  }

  if (preset.thinkingLevel) pi.setThinkingLevel(preset.thinkingLevel);

  if (preset.tools && preset.tools.length > 0) {
    const knownTools = new Set(pi.getAllTools().map((tool) => tool.name));
    const validTools = preset.tools.filter((tool) => knownTools.has(tool));
    const invalidTools = preset.tools.filter((tool) => !knownTools.has(tool));

    if (invalidTools.length > 0) {
      ctx.ui.notify(`Preset ${name}: unknown tools: ${invalidTools.join(", ")}`, "warning");
    }
    if (validTools.length > 0) pi.setActiveTools(validTools);
  }
}

// Tool-name prefixes whose results are untrusted external content. Once one has
// run, the session context may carry injected instructions.
const CONNECTOR_PREFIXES = ["gmail_", "calendar_", "strava_", "granola", "notes_sources"];
const ACTING_TOOLS = new Set(["bash", "edit", "write"]);

export function isConnectorTool(toolName: string): boolean {
  return CONNECTOR_PREFIXES.some((prefix) => toolName.startsWith(prefix));
}

export function presetCanAct(preset: Preset): boolean {
  return (preset.tools ?? []).some((tool) => ACTING_TOOLS.has(tool));
}

export default function presetsExtension(pi: ExtensionAPI) {
  let presets: PresetsConfig = {};
  let activePresetName: string | undefined;
  let activePreset: Preset | undefined;
  let sessionReadUntrustedContent = false;

  // The containment boundary is the session, not the preset: switching a
  // tainted session to an acting preset would let injected content drive
  // tools. Warn and require explicit confirmation.
  async function confirmTaintedSwitch(name: string, preset: Preset, ctx: ExtensionContext): Promise<boolean> {
    if (!sessionReadUntrustedContent || !presetCanAct(preset)) return true;
    return ctx.ui.confirm(
      "Untrusted content in session",
      `This session has read connector content (email, calendar, or activity data), which may carry injected instructions. Switching to "${name}" enables ${(preset.tools ?? []).filter((tool) => ACTING_TOOLS.has(tool)).join("/")}, letting that content drive actions.\n\nSafer: start a fresh session and carry over only what you have read yourself. Switch anyway?`,
    );
  }

  pi.registerFlag("preset", {
    description: "Apply a named preset from ~/.pi/agent/presets.json or .pi/presets.json",
    type: "string",
  });

  pi.registerCommand("preset", {
    description: "Apply a named preset",
    handler: async (args, ctx) => {
      presets = loadPresets(ctx.cwd);
      const requested = args.trim();

      if (requested) {
        const preset = presets[requested];
        if (!preset) {
          ctx.ui.notify(`Unknown preset: ${requested}`, "warning");
          return;
        }
        if (!(await confirmTaintedSwitch(requested, preset, ctx))) return;
        activePresetName = requested;
        activePreset = preset;
        await applyPreset(requested, preset, pi, ctx);
        ctx.ui.notify(`Preset active: ${presetSummary(requested, preset)}`, "info");
        return;
      }

      const names = Object.keys(presets);
      if (names.length === 0) {
        ctx.ui.notify("No presets found", "warning");
        return;
      }

      const choice = await ctx.ui.select(
        "Select preset",
        names.map((name) => (name === activePresetName ? `${name} (active)` : name)),
      );
      if (!choice) return;

      const name = choice.replace(/ \(active\)$/, "");
      const preset = presets[name];
      if (!(await confirmTaintedSwitch(name, preset, ctx))) return;
      activePresetName = name;
      activePreset = preset;
      await applyPreset(name, preset, pi, ctx);
      ctx.ui.notify(`Preset active: ${presetSummary(name, preset)}`, "info");
    },
  });

  pi.on("session_start", async (_event, ctx) => {
    presets = loadPresets(ctx.cwd);
    const settingsManager = (ctx as unknown as { settingsManager?: { getSettings(): PresetSettings } }).settingsManager;
    const settings = (settingsManager?.getSettings() ?? {}) as PresetSettings;
    const requested = (pi.getFlag("preset") as string | undefined) ?? settings.defaultPreset;
    if (!requested) return;

    const preset = presets[requested];
    if (!preset) {
      ctx.ui.notify(`Default preset not found: ${requested}`, "warning");
      return;
    }

    activePresetName = requested;
    activePreset = preset;
    await applyPreset(requested, preset, pi, ctx);
    ctx.ui.notify(`Preset active: ${presetSummary(requested, preset)}`, "info");
  });

  pi.on("tool_execution_end", async (event) => {
    if (isConnectorTool(event.toolName)) sessionReadUntrustedContent = true;
  });

  pi.on("before_agent_start", async (event) => {
    if (!activePresetName || !activePreset?.instructions) return undefined;
    return {
      systemPrompt: `${event.systemPrompt}\n\nActive Pi preset: ${activePresetName}\n${activePreset.instructions}`,
    };
  });
}
