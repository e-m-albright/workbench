import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const REPOSITORY_RE = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const WORKFLOW_RE = /^[A-Za-z0-9_.\/-]+$/;
const INPUT_NAME_RE = /^[A-Za-z0-9_.-]+$/;

export interface WorkflowInput {
	name: string;
	value: string;
}

export interface WorkflowDispatch {
	repository: string;
	workflow: string;
	ref: string;
	inputs: WorkflowInput[];
}

interface RunRecord {
	createdAt?: string;
	url?: string;
}

export function validateDispatch(dispatch: WorkflowDispatch): void {
	if (!REPOSITORY_RE.test(dispatch.repository)) throw new Error("repository must be owner/name");
	if (!WORKFLOW_RE.test(dispatch.workflow) || dispatch.workflow.startsWith("-")) {
		throw new Error("workflow must be a workflow name or path");
	}
	if (!dispatch.ref || dispatch.ref.startsWith("-") || /[\0\r\n]/.test(dispatch.ref)) {
		throw new Error("ref must be a branch or tag name");
	}
	if (dispatch.inputs.length > 20) throw new Error("at most 20 workflow inputs are allowed");
	for (const input of dispatch.inputs) {
		if (!INPUT_NAME_RE.test(input.name)) throw new Error(`invalid input name: ${input.name}`);
		if (input.value.length > 1000 || /\0/.test(input.value)) {
			throw new Error(`invalid value for input: ${input.name}`);
		}
	}
}

export function buildDispatchArgs(dispatch: WorkflowDispatch): string[] {
	validateDispatch(dispatch);
	const args = ["workflow", "run", dispatch.workflow, "--repo", dispatch.repository, "--ref", dispatch.ref];
	for (const input of dispatch.inputs) args.push("--field", `${input.name}=${input.value}`);
	return args;
}

export function confirmationText(dispatch: WorkflowDispatch): string {
	const inputs = dispatch.inputs.length
		? dispatch.inputs.map((input) => `  ${input.name}=${input.value}`).join("\n")
		: "  (none)";
	return [
		`Repository: ${dispatch.repository}`,
		`Workflow: ${dispatch.workflow}`,
		`Ref: ${dispatch.ref}`,
		"Inputs:",
		inputs,
	].join("\n");
}

export function newestRunUrl(stdout: string, dispatchedAt: number): string | undefined {
	let records: RunRecord[];
	try {
		records = JSON.parse(stdout) as RunRecord[];
	} catch {
		return undefined;
	}
	const floor = dispatchedAt - 5000;
	return records.find((record) => {
		const created = Date.parse(record.createdAt ?? "");
		return Number.isFinite(created) && created >= floor && typeof record.url === "string";
	})?.url;
}

async function discoverRunUrl(
	pi: ExtensionAPI,
	dispatch: WorkflowDispatch,
	dispatchedAt: number,
	signal: AbortSignal | undefined,
): Promise<string | undefined> {
	for (let attempt = 0; attempt < 6; attempt++) {
		if (attempt > 0) await new Promise((resolve) => setTimeout(resolve, 1000));
		const result = await pi.exec(
			"gh",
			[
				"run",
				"list",
				"--repo",
				dispatch.repository,
				"--workflow",
				dispatch.workflow,
				"--branch",
				dispatch.ref,
				"--event",
				"workflow_dispatch",
				"--limit",
				"5",
				"--json",
				"createdAt,url",
			],
			{ signal, timeout: 15_000 },
		);
		if (result.code !== 0) return undefined;
		const url = newestRunUrl(result.stdout, dispatchedAt);
		if (url) return url;
	}
	return undefined;
}

export default function githubWorkflowDispatch(pi: ExtensionAPI) {
	pi.registerTool({
		name: "github_workflow_dispatch",
		label: "Dispatch GitHub workflow",
		description:
			"Dispatch one GitHub Actions workflow after interactive confirmation. Shows the exact repository, workflow, ref, and inputs; never dispatches in headless mode.",
		promptSnippet: "github_workflow_dispatch: confirm and run one GitHub Actions workflow",
		promptGuidelines: [
			"Use github_workflow_dispatch instead of gh workflow run after the user approves the exact repository, workflow, ref, and inputs.",
		],
		parameters: Type.Object({
			repository: Type.String({ description: "GitHub owner/name" }),
			workflow: Type.String({ description: "Workflow filename, id, or name" }),
			ref: Type.String({ description: "Branch or tag containing the workflow" }),
			inputs: Type.Optional(
				Type.Array(
					Type.Object({
						name: Type.String(),
						value: Type.String(),
					}),
				),
			),
		}),
		async execute(_id, params, signal, _onUpdate, ctx: ExtensionContext) {
			const dispatch: WorkflowDispatch = { ...params, inputs: params.inputs ?? [] };
			validateDispatch(dispatch);
			if (!ctx.hasUI) throw new Error("workflow dispatch requires interactive confirmation");
			const approved = await ctx.ui.confirm("Dispatch GitHub workflow?", confirmationText(dispatch));
			if (!approved) throw new Error("workflow dispatch declined");

			const dispatchedAt = Date.now();
			const result = await pi.exec("gh", buildDispatchArgs(dispatch), { signal, timeout: 30_000 });
			if (result.code !== 0) throw new Error(result.stderr.trim() || "gh workflow run failed");
			const runUrl = await discoverRunUrl(pi, dispatch, dispatchedAt, signal);
			const text = runUrl
				? `Workflow dispatched: ${runUrl}`
				: "Workflow dispatched; run URL is not visible yet.";
			return { content: [{ type: "text" as const, text }], details: { dispatch, runUrl } };
		},
	});
}
