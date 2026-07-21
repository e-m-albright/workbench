import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { truncateToWidth } from "@earendil-works/pi-tui";

const RESET = "\x1b[0m";
const PI_LINES = [
	"████████████",
	"   ███  ███",
	"   ███  ███",
	"   ███  ███",
];

// Dotfiles topaz + Workbench ruby = Pi orange: the coding surface made from both.
const ORANGE_STOPS = [
	[255, 220, 170],
	[255, 159, 67],
	[229, 83, 35],
	[145, 45, 13],
] as const;

function mixColor(position: number): readonly [number, number, number] {
	const scaled = Math.min(Math.max(position, 0), 0.999) * (ORANGE_STOPS.length - 1);
	const index = Math.floor(scaled);
	const fraction = scaled - index;
	const start = ORANGE_STOPS[index];
	const end = ORANGE_STOPS[index + 1];
	return [
		Math.round(start[0] + (end[0] - start[0]) * fraction),
		Math.round(start[1] + (end[1] - start[1]) * fraction),
		Math.round(start[2] + (end[2] - start[2]) * fraction),
	];
}

function gradient(line: string): string {
	if (process.env.NO_COLOR) return line;
	const width = Math.max(1, line.length - 1);
	return [...line]
		.map((character, column) => {
			const [red, green, blue] = mixColor(column / width);
			return `\x1b[38;2;${red};${green};${blue}m${character}`;
		})
		.join("") + RESET;
}

export default function (pi: ExtensionAPI) {
	pi.on("session_start", async (_event, ctx) => {
		if (!ctx.hasUI) return;
		ctx.ui.setHeader((_tui, theme) => ({
			dispose() {},
			invalidate() {},
			render(width: number): string[] {
				const mark = PI_LINES.map((line) => truncateToWidth(gradient(line), width));
				if (width >= 30) {
					mark[1] += theme.fg("dim", "   coding agent");
				}
				return mark;
			},
		}));
	});
}
