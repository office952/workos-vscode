import type { ReactNode } from "react";

/**
 * Intake V6 presentation tokens — aliases to WorkOS semantic `wo-*` surfaces.
 * Follows html.light / html.dark via CSS vars (R4/R7 Day honesty).
 * Mapping mirrors productSystemSurfaces / R4 hex sweep.
 */
export const v6 = {
	page: "flex min-h-full flex-col bg-wo-surface-inset text-wo-text-primary text-[12px] leading-relaxed",
	shell: "border-wo-border-strong",
	main: "w-full max-w-none flex-1 px-5 pt-5 pb-4 sm:px-6 lg:px-8",
	grid: "grid gap-4",
	gridTwoCol: "grid gap-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] xl:gap-5",
	layersFullWidthGrid:
		"grid gap-5 lg:grid-cols-[minmax(0,1.85fr)_minmax(280px,380px)] xl:grid-cols-[minmax(0,2fr)_minmax(300px,400px)] 2xl:gap-6",
	layersStepGrid:
		"grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(280px,340px)] xl:grid-cols-[minmax(0,1fr)_minmax(300px,360px)] 2xl:gap-6",
	confirmStepGrid:
		"grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(280px,320px)] xl:grid-cols-[minmax(0,1fr)_minmax(300px,340px)] 2xl:gap-6",
	card: "rounded-[10px] border border-wo-border-strong bg-wo-surface-raised p-4 sm:p-5",
	cardCompact: "rounded-[10px] border border-wo-border-strong bg-wo-surface-raised p-3 sm:p-4",
	mono: "font-mono",
	screenTitle: "text-[15px] font-semibold leading-snug text-wo-text-primary",
	sectionTitle: "text-[14px] font-semibold leading-snug text-wo-text-secondary",
	zoneTitle: "text-[12px] font-semibold text-wo-text-muted",
	sectionDesc: "mt-0.5 text-[11px] leading-relaxed text-wo-text-dim",
	label: "mb-1 block text-[12px] font-medium text-wo-text-dim",
	metricLabel: "text-[11px] font-medium text-wo-text-dim",
	helper: "text-[11px] text-wo-text-dim",
	metricValue: "text-[15px] font-semibold leading-tight text-wo-text-primary",
	input:
		"w-full rounded border border-wo-border-strong bg-wo-surface-input px-3 py-2 text-[12px] text-wo-text-secondary outline-none focus:border-blue-500/50",
	btnPrimary:
		"rounded-md bg-sky-500/15 px-4 py-2 text-[12px] font-bold text-sky-700 border border-sky-500/30 hover:bg-sky-500/25 dark:text-sky-300",
	btnConfirm:
		"rounded-md bg-gradient-to-b from-emerald-500 to-emerald-600 px-5 py-2.5 text-[12px] font-bold text-white shadow-[0_4px_14px_rgba(16,185,129,0.35)] border border-emerald-400/40 hover:from-emerald-400 hover:to-emerald-500 disabled:cursor-not-allowed disabled:border-emerald-800/30 disabled:from-emerald-900/40 disabled:to-emerald-900/60 disabled:text-emerald-200/40 disabled:shadow-none",
	btnGhost:
		"rounded-md border border-wo-border-strong bg-wo-hover px-4 py-2 text-[12px] font-semibold text-wo-text-secondary hover:border-sky-500/30",
} as const;

/**
 * Scoped Configurator Design System pilot tokens (letters Finisaje + Iluminare).
 * Do not replace `v6` — Montaj and page shell stay on the baseline tokens.
 */
export const v6Pilot = {
	clusterTitle: "text-[16px] font-semibold leading-snug text-wo-text-primary",
	sectionTitle: "text-[15px] font-semibold leading-snug text-wo-text-primary",
	zoneTitle: "text-[14px] font-semibold leading-snug text-wo-text-secondary",
	decisionTitle: "text-[13px] font-semibold text-wo-text-secondary",
	label: "mb-1 block text-[13px] font-medium text-wo-text-muted",
	body: "text-[14px] leading-relaxed text-wo-text-secondary",
	helper: "text-[12px] leading-relaxed text-wo-text-dim",
	technical: "text-[11px] leading-relaxed text-wo-text-dim",
	select:
		"h-8 w-full rounded border border-wo-border-strong bg-wo-surface-input px-2.5 py-1 text-[13px] text-wo-text-secondary outline-none focus:border-sky-500/40",
	resultPanel:
		"rounded-md border border-wo-border-strong/80 bg-wo-surface-inset/70 px-3 py-2.5 space-y-1.5",
	resultLabel: "text-[12px] font-semibold uppercase tracking-wide text-wo-text-dim",
	resultValue: "text-[14px] font-semibold tabular-nums text-wo-text-primary",
	anatomyZone:
		"rounded-md border border-wo-border-strong/60 bg-wo-surface-raised/40 px-2.5 py-2",
} as const;

export type AtomsBadgeTone = "ok" | "pending" | "action" | "muted";

export function AtomsBadge({
	tone,
	children,
}: {
	tone: AtomsBadgeTone;
	children: ReactNode;
}) {
	const cls =
		tone === "ok"
			? "bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/25 dark:text-emerald-400"
			: tone === "pending"
				? "bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-500/10 dark:border-amber-500/25 dark:text-amber-300"
				: tone === "action"
					? "bg-sky-50 border-sky-200 text-sky-800 dark:bg-sky-500/10 dark:border-sky-500/25 dark:text-sky-300"
					: "bg-slate-100 border-slate-200 text-slate-600 dark:bg-slate-500/10 dark:border-slate-500/20 dark:text-slate-400";
	return (
		<span className={`inline-flex rounded px-2 py-0.5 text-[11px] font-semibold border ${cls}`}>
			{children}
		</span>
	);
}
