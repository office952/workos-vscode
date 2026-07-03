import type { ReactNode } from "react";

export const v6 = {
	page: "flex min-h-full flex-col bg-[#0A0F1A] text-[#F1F5F9] text-[12px] leading-relaxed",
	shell: "border-[#2A3548]",
	main: "w-full max-w-none flex-1 px-5 pt-5 pb-4 sm:px-6 lg:px-8",
	grid: "grid gap-4",
	gridTwoCol: "grid gap-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] xl:gap-5",
	layersFullWidthGrid:
		"grid gap-5 lg:grid-cols-[minmax(0,1.85fr)_minmax(280px,380px)] xl:grid-cols-[minmax(0,2fr)_minmax(300px,400px)] 2xl:gap-6",
	layersStepGrid:
		"grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(280px,340px)] xl:grid-cols-[minmax(0,1fr)_minmax(300px,360px)] 2xl:gap-6",
	confirmStepGrid:
		"grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(280px,320px)] xl:grid-cols-[minmax(0,1fr)_minmax(300px,340px)] 2xl:gap-6",
	card: "rounded-[10px] border border-[#2A3548] bg-[#111827] p-4 sm:p-5",
	cardCompact: "rounded-[10px] border border-[#2A3548] bg-[#111827] p-3 sm:p-4",
	mono: "font-mono",
	screenTitle: "text-[15px] font-semibold leading-snug text-slate-100",
	sectionTitle: "text-[14px] font-semibold leading-snug text-slate-200",
	zoneTitle: "text-[12px] font-semibold text-slate-400",
	sectionDesc: "mt-0.5 text-[11px] leading-relaxed text-slate-500",
	label: "mb-1 block text-[12px] font-medium text-slate-500",
	metricLabel: "text-[11px] font-medium text-slate-500",
	helper: "text-[11px] text-slate-500",
	metricValue: "text-[15px] font-semibold leading-tight text-slate-100",
	input:
		"w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-3 py-2 text-[12px] text-slate-200 outline-none focus:border-blue-500/50",
	btnPrimary:
		"rounded-md bg-sky-500/15 px-4 py-2 text-[12px] font-bold text-sky-300 border border-sky-500/30 hover:bg-sky-500/25",
	btnConfirm:
		"rounded-md bg-gradient-to-b from-emerald-500 to-emerald-600 px-5 py-2.5 text-[12px] font-bold text-white shadow-[0_4px_14px_rgba(16,185,129,0.35)] border border-emerald-400/40 hover:from-emerald-400 hover:to-emerald-500 disabled:cursor-not-allowed disabled:border-emerald-800/30 disabled:from-emerald-900/40 disabled:to-emerald-900/60 disabled:text-emerald-200/40 disabled:shadow-none",
	btnGhost:
		"rounded-md border border-[#2A3548] bg-[#1E293B] px-4 py-2 text-[12px] font-semibold text-slate-300 hover:border-sky-500/30",
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
			? "bg-emerald-500/10 border-emerald-500/25 text-emerald-400"
			: tone === "pending"
				? "bg-amber-500/10 border-amber-500/25 text-amber-300"
				: tone === "action"
					? "bg-sky-500/10 border-sky-500/25 text-sky-300"
					: "bg-slate-500/10 border-slate-500/20 text-slate-400";
	return (
		<span className={`inline-flex rounded px-2 py-0.5 text-[11px] font-semibold border ${cls}`}>
			{children}
		</span>
	);
}