import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const RESET = "\x1b[0m";
const ORANGE = "\x1b[38;2;255;159;67m";

export default function (pi: ExtensionAPI) {
	pi.on("session_start", async (_event, ctx) => {
		if (!ctx.hasUI) return;
		ctx.ui.setHeader(() => ({
			dispose() {},
			invalidate() {},
			render(): string[] {
				return [process.env.NO_COLOR ? "π" : `${ORANGE}π${RESET}`];
			},
		}));
	});
}
